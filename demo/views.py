from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def snatch_view(request):
    return HttpResponse('this is snatch tset')

def open_view(request):
    return HttpResponse('this is open tset')

def get_wall_list_view(request):
    return HttpResponse('this is get_wall_list tset')