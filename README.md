## Задачи:

### Аналитика:

1) Подумать, каким образом их можно систематизировать, какой вид аналитики мы можем получить из этих данных, предложить примерный вид таблицы.

### Более инженерная часть

2) Взять total_balance всего кошелька (полученного через апи)

    Запустить простой скрипт, который будет подгружать значение total_balance всего кошелька и отправлять его либо в телеграмм, либо в дискорд, либо в google sheet.


3) *Доп баллы - подключить отправку total_balance в источник по команде извне. При отправке команды в чате тг/дискорда к примеру.




## Установка:

1) Установить зависимости: `pip install -r requirements.txt`
2) Создать / добавить в корень проекта `creds.json`:
    ```json
    {
        "debunk_api": {
            "access_key": "..."
        },
        "discord": {
            "webhook_url": "...",
            "bot_token": "..."
        }
    }
    ```


## Решение:

2) Пример команды, для отправки __total_balance__ в дискорд сервер: `python main.py --output discord`
    
    Для вызова справки: `python main.py --help`

3) `python main.py --host` - для старта fastapi и дискорд бота.

    Дождаться вывода сообщений:
    ```
    INFO:     Started server process [79919]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
    2025-02-11 17:11:19,709: INFO: Shard ID None has connected to Gateway (Session ID: 2e4bcae2809ab7ddace9929ed39e8fe9).
    2025-02-11 17:11:22,136: INFO: Logged in bot1338845619636273194 as (ID: 1338845619636273194)
    ```

    Ссылка на сервер: https://discord.gg/aHW4Nrp4

    Запросы отправляются по команде `/debunk_total_balance`

    `http://localhost:8000/docs` - по этой ссылке будет доступна документации по API, оттуда же можно отправлять тестовые запросы