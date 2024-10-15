from environs import Env

env = Env()
env.read_env()


bot_token: str = env.str('BOT_TOKEN', default='')
gpt_token: str = env.str('BOT_TOKEN', default='')
elastic_password: str = env.str('ELASTIC_PASSWORD', default='')

elk_index = 'llmds_storage'
elk_url = 'https://localhost:9200'
ca_certs = 'src/configs/ca/http_ca.crt'

