import os

class Config:
    def __init__(self):
        # .env файлын жүктеу
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        print(f"Loading .env from: {env_path}")
        print(f"File exists: {os.path.exists(env_path)}")
        
        # Файлды тікелей оқу және env переменныйларын орнату
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                        print(f"Setting env var: {key}={value}")
        
        # Конфигурация параметрлерін алу
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN')
        self.CHANNEL_ID = os.environ.get('CHANNEL_ID')
        
        print(f"CHANNEL_ID from env: {self.CHANNEL_ID}")
        print(f"All env vars: {dict(os.environ)}")
        
        # Параметрлердің бар-жоғын тексеру
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN табылмады")
            
        if not self.CHANNEL_ID:
            raise ValueError("CHANNEL_ID табылмады")
            
        # CHANNEL_ID санға айналдыру
        try:
            self.CHANNEL_ID = int(self.CHANNEL_ID)
            print(f"CHANNEL_ID converted: {self.CHANNEL_ID}")
        except ValueError:
            raise ValueError("CHANNEL_ID сан болуы керек")
