from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.home, name="DigiShop Homepage"),
    path('withdraws/', views.withdraw_table, name="Table of all pending withdraws"),
    path('withdraws/data/', views.grab_withdraw_requests, name="Grabs all penidn gtable data"),
    path('withdraws/mark/', views.mark_withdraw_as_sent, name="Grabs all penidn gtable data"),
    path('todolist/', views.grab_todo_list, name="Grabs all todo items"),
    path('todolist/add/', views.create_discussion, name="Adds a todo item"),
    path('todo/discussion/', views.discussion_page, name="Discussion Page"),
    path('todo/discussion/messages/', views.get_discussion_messages, name="Discussion Page Messages"),
    path('todo/discussion/messages/send/', views.add_discussion_message, name="Add discussion message")

]
