# LLMDS
<h4>RAG-система (Автоматизированая система анализа и ответов по материалам)</h4>
___
Для начала работы необходимо создать файл `.env` по пути: `src/configs/` со следующим содержанием

<code>ELASTIC_PASSWORD=</code><br />
<code>BOT_TOKEN=</code><br />
<code>GPT_TOKEN=</code><br />

После знака `=` без пробела и доп символов заполнить поля.<br>
`ELASTIC_PASSWORD` - Пароль от хранилища данных (elasticsearch).<br>
`BOT_TOKEN` - API token для подключения к боту, нужно создать его через тг бота `@BotFather`<br>
`GPT_TOKEN` - API token для подключения к ChatGPT<br>