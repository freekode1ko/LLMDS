# Автоматизированная система анализа и ответов по материалам

Для запуска надо:

1) Клонировать репозиторий на локальный компьютер.
2) Установить python 3.12.7 x64.
3) Создать виртульное окружение.
4) Установить зависимости `python -m pip install -r requirements.txt`.
<br>P.S. Если возникнит ошибка pip `AttributeError: module 'pkgutil' has no attribute 'ImpImposter'` выполнить следубщие команды: `python -m ensurepip --upgrade`, `python -m pip install --upgrade setuptools`, `python -m pip install -r requirements.txt`.
5) Соберите docker контейнер с ElasticSearch по команде 'docker run -p 9200:9200 -d -m 2GB -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.http.ssl.enabled=false" elasticsearch:8.12.1'.
<br>P.S. Если хочется, можно использовать свой уже готовый ELK, для этого надо положить сертификат сюда: `src/configs/ca/http_ca.crt` и раскомитить 2 строки (14, 15) в `src/modules/elastic.py` 
6) Создай файл `.env` по пути: `src/configs/` со следующим содержанием.

  <code>ELASTIC_PASSWORD=</code><br />
  <code>ELK_URL=</code><br />
  <code>BOT_TOKEN=</code><br />
  <code>GPT_TOKEN=</code><br />
  <code>GPT_MODEL=</code><br />

После знака `=` без пробела и доп символов заполнить поля.<br>
`ELASTIC_PASSWORD` - Пароль от хранилища данных (нужно убрать, если использовалась командой установки ELK из инструкции).<br>
`ELK_URL` - Адрес для elasticsearch (нужно убрать, если использовалась командой установки ELK из инструкции).<br>
`BOT_TOKEN` - API token для подключения к боту, нужно создать его через тг бота `@BotFather`<br>
`GPT_TOKEN` - API token для подключения к ChatGPT<br>
`GPT_MODEL` - Наименование ChatGPT модели подключения (Рекомендуется gpt-4o)<br>
  
7) Запустите bot_runner.py
