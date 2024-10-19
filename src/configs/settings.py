from environs import Env

env = Env()
env.read_env()

LOG_LEVEL_DEBUG = 10
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 30
LOG_LEVEL_ERROR = 40
LOG_LEVEL_CRITICAL = 50

log_lvl = LOG_LEVEL_INFO

emd_count_docs = 4
bot_token: str = env.str('BOT_TOKEN', default='')
gpt_model: str = env.str('GPT_MODEL', default='gpt-4o-mini')
gpt_token: str = env.str('GPT_TOKEN', default='')
elastic_password: str = env.str('ELASTIC_PASSWORD', default='')
elk_url: str = env.str('ELK_URL', default='http://localhost:9200')
elk_index: str = env.str('ELK_INDEX', default='llmds_storage')
ca_certs: str = env.str('ELK_CERTS', default='src/configs/ca/http_ca.crt')

