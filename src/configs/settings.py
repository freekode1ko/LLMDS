from environs import Env

env = Env()
env.read_env()

emd_count_docs = 4
bot_token: str = env.str('BOT_TOKEN', default='')
gpt_token: str = env.str('GPT_TOKEN', default='')
elastic_password: str = env.str('ELASTIC_PASSWORD', default='')
elk_url: str = env.str('ELK_URL', default='https://localhost:9200')
elk_index: str = env.str('ELK_INDEX', default='llmds_storage')
ca_certs: str = env.str('ELK_CERTS', default='src/configs/ca/http_ca.crt')

