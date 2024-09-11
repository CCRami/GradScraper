# scraperapp/views.py
import os
import json
from django.shortcuts import get_object_or_404, redirect, render
from .tasks import scrape_linkedin_task
from .models import ScrapingProgress
from scraperapp.models import Company, Person, CustomUser
from django.http import HttpResponseBadRequest, JsonResponse
from redis import Redis
from django.conf import settings
from django.db.models import Prefetch
from django.db.models import Count
import configparser
from django.db.models import Count, Sum, F, ExpressionWrapper
from decimal import Decimal
import datetime
import xml.etree.ElementTree as ET
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from django.contrib.auth import logout
from django.contrib.auth import login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required

def get_progress_data_from_redis(redis_conn):
    scraped_data = redis_conn.get('scraped_data')
    data = json.loads(scraped_data) if scraped_data else []

    scraping_progress = redis_conn.get('scraping_progress')
    if scraping_progress:
        progress_info = json.loads(scraping_progress)
        progress = progress_info.get('progress', 0)
        step = progress_info.get('step', 0)
        total_steps = progress_info.get('total_steps', 0)
    else:
        progress = 0
        step = 0
        total_steps = 0

    return data, progress, step, total_steps



@login_required
def start_scraping(request):
    if request.method == 'POST':
        try:
            st_num = int(request.POST.get('st_num'))
            year = int(request.POST.get('year'))
            label = request.POST.get('label')
            
            # Get current datetime for the start time
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Initialize Redis connection and set progress
            redis_conn = Redis(host='localhost', port=6379, db=1)
            redis_conn.set('scraping_progress', json.dumps({'progress': 0, 'step': 0, 'total_steps': st_num}))
            redis_conn.set('scraped_data', json.dumps([]))

            # Save scraping session details to XML
            xml_file = 'scraping_history.xml'
            if not os.path.exists(xml_file):
                root = ET.Element("scraping_history")
            else:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
            session = ET.SubElement(root, "session")
            ET.SubElement(session, "label").text = label
            ET.SubElement(session, "st_num").text = str(st_num)
            ET.SubElement(session, "year").text = str(year)
            ET.SubElement(session, "start_time").text = start_time
            ET.SubElement(session, "end_time").text = ""  # Leave this empty for now
            
            # Save or update the XML file
            tree = ET.ElementTree(root)
            tree.write(xml_file)

            # Start the scraping task
            scrape_linkedin_task.delay(st_num, year)
            return render(request, 'scraperapp/progress.html')
        
        except ValueError:
            return HttpResponseBadRequest("Invalid input. Please provide valid numbers.")
    else:
        return redirect('results')
    
def update_end_time(request):
    xml_file = 'scraping_history.xml'
    if os.path.exists(xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        # Find the last session
        last_session = root.findall('session')[-1]
        # Update the end_time
        last_session.find('end_time').text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Save the XML file
        tree.write(xml_file)
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "error", "message": "Scraping history file not found."}, status=400)

def get_progress_data(request):
    redis_conn = Redis(host='localhost', port=6379, db=1)
    scraped_data_json = redis_conn.get('scraped_data')
    _, progress, step, total_steps = get_progress_data_from_redis(redis_conn)
    scraped_data = json.loads(scraped_data_json) if scraped_data_json else []

    return JsonResponse({
        'scraped_data': scraped_data,
        'progress': progress, 'step': step, 'total_steps': total_steps
    })
    
def getdata():
    # Define the URL to match and the replacement URL
    match_url = "https://media.licdn.com/dms/image/v2/D4D03AQHoHh3c5w12xA/"
    replacement_url = "https://i.imgur.com/mUtO8vh.jpg"
    all_persons_data = Person.objects.all().values('url', 'email', 'name', 'title', 'location', 'company__name', 'img_url')
    processed_data = []
    for person in all_persons_data:
        if person['img_url'].startswith(match_url):
            person['img_url'] = replacement_url
        processed_data.append(person)
    
    return processed_data
@login_required
def results(request):
    order = request.GET.get('order', 'asc')
    search_query = request.GET.get('q', '')
    data = getdata()

    if search_query:
        data = [d for d in data if search_query.lower() in d['name'].lower()]

    if order == 'asc':
        data = sorted(data, key=lambda x: x['name'])
    elif order == 'desc':
        data = sorted(data, key=lambda x: x['name'], reverse=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'data': data})

    return render(request, 'scraperapp/results.html', {'data': data, 'order': order})
@login_required
def resultsbycompany(request):
    companies = Company.objects.prefetch_related(
        Prefetch('person_set', queryset=Person.objects.all())
    )
    return render(request, 'scraperapp/resultsbycompany.html', {'companies': companies})

def get_company_members(request):
    company_id = request.GET.get('company_id')
    if company_id:
        members = Person.objects.filter(company_id=company_id).values('name', 'url', 'email','title', 'location')
        return JsonResponse({'members': list(members)})
    return JsonResponse({'members': []})

@login_required
def delete_company(request):
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                company.delete()
                return JsonResponse({'success': True})
            except Company.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Company not found.'})
        return JsonResponse({'success': False, 'message': 'Invalid company ID.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def index(request):
    today = datetime.now()
    formatted_date = today.strftime("%a, %d %b %Y")
    config = configparser.ConfigParser()
    config.read('web.config')
    average_salary = Decimal(config.get('Settings', 'average_salary', fallback='0'))
    currency = config.get('Settings', 'currency', fallback='USD')


    excluded_employees = Person.objects.filter(
        company__name__in=['ESPRIT', 'Ecole Supérieure Privée d\'Ingénierie et de Technologies - ESPRIT']
    ).count()

    total_employees = Person.objects.count()
    included_employees = total_employees - excluded_employees


    total_salary = included_employees * average_salary

    if total_salary >= Decimal(1_000_000):
        total_salary_display = f"{total_salary/Decimal(1_000_000):.1f}M"
    else:
        total_salary_display = f"{total_salary:.0f}"

    company_employee_counts = Company.objects.annotate(employee_count=Count('person')).exclude(
        name__in=['ESPRIT', 'Ecole Supérieure Privée d\'Ingénierie et de Technologies - ESPRIT']
    )

    chart_data = {
        'labels': [company.name for company in company_employee_counts],
        'data': [company.employee_count for company in company_employee_counts],
    }

    return render(request, 'scraperapp/index.html', {
        'num_students': total_employees,
        'num_companies': Company.objects.count(),
        'excluded_employees' : excluded_employees,
        'chart_data': json.dumps(chart_data),
        'total_salary': total_salary_display,
        'currency': currency,
        'date': formatted_date,
    })

@login_required
def settings(request):
    config = configparser.ConfigParser()
    config_file_path = 'web.config'

    if request.method == 'POST':
        average_salary = request.POST.get('average_salary')
        currency = request.POST.get('currency')

        config['Settings'] = {
            'average_salary': average_salary,
            'currency': currency,
        }

        with open(config_file_path, 'w') as configfile:
            config.write(configfile)

    else:

        config.read(config_file_path)
        average_salary = config.get('Settings', 'average_salary', fallback='')
        currency = config.get('Settings', 'currency', fallback='')

    return render(request, 'scraperapp/settings.html', {
        'average_salary': average_salary,
        'currency': currency,
    })
    
@login_required    
def delete_session(request):
    label_to_delete = request.POST.get('label')
    
    # Parse the XML file
    tree = ET.parse('scraping_history.xml')  # Update with the correct path
    root = tree.getroot()
    
    # Find the session to delete
    for session in root.findall('session'):
        label = session.find('label').text
        if label == label_to_delete:
            root.remove(session)
            tree.write('scraping_history.xml')  # Save the updated XML file
            break
    
    return redirect(reverse('history'))
@login_required    
def history(request):
    tree = ET.parse('scraping_history.xml')  # Update with the correct path to your XML file
    root = tree.getroot()
    
    sessions = []
    for session in root.findall('session'):
        label = session.find('label').text
        st_num = session.find('st_num').text
        year = session.find('year').text
        start_time = session.find('start_time').text
        end_time = session.find('end_time').text
        sessions.append({
            'label': label,
            'year': year,
            'st_num': st_num,
            'start_time': start_time,
            'end_time': end_time,
        })
    return render(request, 'scraperapp/history.html', {'sessions': sessions})
    
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/index')  # Redirect to dashboard after registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'scraperapp/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/index')  # Redirect to dashboard after login
            else:
                form.add_error(None, 'Invalid email or password.')  # Add a general error
    else:
        form = LoginForm()
    return render(request, 'scraperapp/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('/login') 