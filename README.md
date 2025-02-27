## Задачи:

### Аналитика:

1) Подумать, каким образом их можно систематизировать, какой вид аналитики мы можем получить из этих данных, предложить примерный вид таблицы.

### Более инженерная часть

2) Взять total_balance всего кошелька (полученного через апи)

    Запустить простой скрипт, который будет подгружать значение total_balance всего кошелька и отправлять его либо в телеграмм, либо в дискорд, либо в google sheet.


3) *Доп баллы - подключить отправку total_balance в источник по команде извне. При отправке команды в чате тг/дискорда к примеру.




## Установка:

1) Установить зависимости: `pip install -r requirements.txt`
2) Добавить в корень проекта `creds.json`. Пример файла:
    ```json
    {
        "debank_api": {
            "access_key": "..."
        },
        "discord": {
            "webhook_url": "...",
            "bot_token": "..."
        }
    }
    ```


## Решение:
1) Для аналитики я спроектировал следующую таблицу:
    
    | token_name                  | token_symbol | protocol_name | chain | position_type | token_type | quantity          | price_usd          | total_value_usd     | unlock_at   |
    |-----------------------------|-------------|---------------|-------|---------------|------------|-------------------|--------------------|---------------------|-------------|
    | Synthetix Network Token     | SNX         | Aave V2       | eth   | Lending       | supply     | 0.002623760132171 | 0.9969500317109995 | 0.00261575774696985 | 0           |
    | USD Coin                    | USDC        | Aave V2       | eth   | Lending       | supply     | 0.007215          | 1.0000000000000000 | 0.00721500000000000 | 0           |
    | Aave Token                  | AAVE        | Aave V2       | eth   | Lending       | reward     | 0.000000216455321 | 244.7515372766987  | 0.0000529777726130  | 0           |
    | Agility                     | AGI         | Agility       | eth   | Locked        | supply     | 3242.683184466888 | 0.0013189569602940 | 4.2769595561807720  | 1682732699  |
    | Agility                     | AGI         | Agility       | eth   | Locked        | supply     | 3265.454934635906 | 0.0013189569602940 | 4.3069945145642730  | 1682913023  |
    | Agility                     | AGI         | Agility       | eth   | Locked        | supply     | 1544.610275904610 | 0.0013189569602940 | 2.0372744743459537  | 1683037499  |
    
    В таблице представлены детальные данные о токенах, которые хранятся на кошельке. 
    
    Для каждого токена указаны: 
    - название (str): для удобного поиска
    - символ (str): уникальный идентификатор
    - протокол (str): в каком протоколе используется токeн 
    - сеть (str): в какой сети хранится токен и протокол
    - тип позиции (str): в какой позиции используется протокол (например, "lending", "locked", "vesting")
    - тип токена (str): тип токена (например, "supply", "reward" или "borrow")
    - количество (float)
    - цена в USD (float)
    - общая стоимость в USD (float)
    - дата разблокировки (float): timestamp дата, когда токен будет разблокирован (если есть)

    Вариант анализа:
    - разбивка и суммация по типам токенов ('supply', "reward", "borrow")
    - эффективность лендинга (reward_balance / collateral_balance)
    - соотношение долга и обеспечения (debt_balance / collateral_balance)
    - группировка, по сетям, протокалам внутри них и по типу позиции для нескольких токенов
    - аггрегировать данные по дате разблокировки, посчитать уровень ликвидности
    - подсчет доли каждого токена/протокола/сети в общем портфеле 
    

2)  Для взаимодействия с API DeBank я использовал библиотеку __aiohtttp__ и эндпоинт: `/v1/user/all_complex_protocol_list`. Асинхронность позволяет ускорить обработку данных при большом количестве запросов и не блокировать поток выполнения.
    
    Для отправки сообщений в дискорд сервер, я использовал __Discord Webhook__. Что позволяет отправлять сообщения в каналы без необходимости создания бота.

    В результате выполнения скрипта, будет отправлено сообщение в о кошельке, датой и временем, когда были получены данные, а также __total_balance__ в виде csv файла.

    Пример сообщения:
    
    Total balance of `profile_id` profile at `date` UTC
    | protocol_chain              | Reward Balance | Debt Balance | Collateral Balance | Net Balance | Total Balance USD |
    |-----------------------------|---------------|-------------|--------------------|------------|------------------|
    | 100x (blast)               | 0             | 0           | 0.001742           | 0.001742   | 0.001742         |
    | Aave V2 (eth)              | 0.000054      | 0           | 0.009866           | 0.009866   | 0.009919         |
    | Agility (eth)              | 0             | 0           | 10.749358          | 10.749358  | 10.749358        |
    | ArbiNYAN (arb)             | 0.02087       | 0           | 0.013372           | 0.013372   | 0.034242         |
    | Asymmetry Finance (eth)    | 0             | 0           | 33361.42611        | 33361.42611| 33361.42611      |
    
    Для отправки __total_balance__ в дискорд сервер, необходимо выполнить команду: `python main.py --output discord`
    

3) Для реализации отправки __total_balance__ по команде извне, я воспользовался асинхронным фреймворком __FastAPI__ и написал небольшой веб-сервер, что позволяет унифицировать обмен данными с разных источников и упростить интеграцию с другими сервисами в будущем.

    Я реализовал отправку __total_balance__ по команде из дискорд сервера. (На данный момент реализована отправка только в дискорд)

    Для запуска сервера и дискорд бота, необходимо выполнить команду: `python main.py --host`

    Дождаться вывода сообщений:
    ```
    INFO:     Started server process [79919]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
    2025-02-11 17:11:19,709: INFO: Shard ID None has connected to Gateway (Session ID: 2e4bcae2809ab7ddace9929ed39e8fe9).
    2025-02-11 17:11:22,136: INFO: Logged in bot1338845619636273194 as (ID: 1338845619636273194)
    ```

    Ссылка на дискорд сервер: https://discord.gg/aHW4Nrp4

    Запросы отправляются по команде бота: `/debank_total_balance`

    `http://localhost:8000/docs` - по этой ссылке будет доступна документации по API, оттуда же можно отправлять тестовые запросы