{% extends "base.html" %}
{% block title %}Админ{% endblock %}
{% block content %}
  <h1>Админ-панель</h1>
  <ul>
    <li>Объявлений: {{total_ads}}</li>
    <li>Сделок: {{total_trades}}</li>
    <li>Ожидают оплаты: {{pending}}</li>
    <li>В спорах: {{disputes}}</li>
  </ul>
{% endblock %}
