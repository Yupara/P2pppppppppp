<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>Мои сделки</title>
  <style>
    body {
      background-color: #002b26;
      color: white;
      font-family: Arial, sans-serif;
      padding: 20px;
    }

    h1 {
      text-align: center;
      color: #90EE90;
    }

    .order {
      background-color: #003f35;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 15px;
    }

    .order p {
      margin: 5px 0;
    }

    .status {
      font-weight: bold;
    }

    .status.paid {
      color: orange;
    }

    .status.confirmed {
      color: green;
    }

    .status.disputed {
      color: red;
    }

    .button {
      background-color: #00796b;
      color: white;
      padding: 5px 10px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    .button:hover {
      background-color: #004d40;
    }
  </style>
</head>
<body>
  <h1>Мои сделки</h1>
  <div id="ordersContainer">
    <p>Загрузка...</p>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      fetch('/api/orders/mine', {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('token')
        }
      })
      .then(res => res.json())
      .then(data => {
        const container = document.getElementById('ordersContainer');
        if (!data.length) {
          container.innerHTML = '<p>У вас пока нет сделок.</p>';
          return;
        }

        container.innerHTML = '';
        data.forEach(order => {
          const div = document.createElement('div');
          div.className = 'order';
          div.innerHTML = `
            <p><strong>Тип:</strong> ${order.type === 'buy' ? 'Покупка' : 'Продажа'}</p>
            <p><strong>Сумма:</strong> ${order.amount} USDT</p>
            <p><strong>Цена:</strong> ${order.price} ₽</p>
            <p><strong>Статус:</strong> <span class="status ${order.status}">${order.status}</span></p>
            <button class="button" onclick="goToTrade(${order.id})">Открыть</button>
          `;
          container.appendChild(div);
        });
      });

      function goToTrade(orderId) {
        window.location.href = '/trade?id=' + orderId;
      }
    });
  </script>
</body>
</html>
