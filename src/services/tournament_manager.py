import json
import os
from src.services.country_db import get_all_countries

class TournamentManager:
    DB_PATH = "tournament_state.json"

    def __init__(self):
        self.qualified_countries = []  # Список стран, прошедших квалификацию
        self.current_round = 1
        self.max_qualification_rounds = 50
        self.is_tournament_phase = False  # Переключится в True после 50 раундов
        
        self.load_state()

    def load_state(self):
        """Загружает состояние турнира из JSON файла, если он существует."""
        if os.path.exists(self.DB_PATH):
            try:
                with open(self.DB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.qualified_countries = data.get("qualified_countries", [])
                    self.current_round = data.get("current_round", 1)
                    self.is_tournament_phase = data.get("is_tournament_phase", False)
                    print(f" Состояние турнира загружено. Раунд: {self.current_round}, Квалифицировано стран: {len(self.qualified_countries)}")
            except Exception as e:
                print(f"Ошибка загрузки БД турнира: {e}")
                self.save_state()
        else:
            self.save_state()

    def save_state(self):
        """Сохраняет текущее состояние турнира в JSON файл."""
        data = {
            "qualified_countries": self.qualified_countries,
            "current_round": self.current_round,
            "is_tournament_phase": self.is_tournament_phase
        }
        try:
            with open(self.DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения БД турнира: {e}")

    def get_available_countries(self):
        """Возвращает список стран для текущего раунда."""
        all_countries = get_all_countries()
        
        if self.is_tournament_phase:
            # Если идет турнир — участвуют ТОЛЬКО те, кто прошел квалификацию
            return self.qualified_countries.copy()
        else:
            # Если идет квалификация — исключаем уже прошедшие флаги
            return [c for c in all_countries if c not in self.qualified_countries]

    def register_winner(self, country_code):
        """Регистрирует последний оставшийся флаг."""
        country_code = country_code.lower()
        
        if not self.is_tournament_phase:
            if country_code not in self.qualified_countries:
                self.qualified_countries.append(country_code)
                print(f" Флаг {country_code.upper()} ПРОШЕЛ квалификацию в раунде {self.current_round}!")
            
            self.current_round += 1
            if self.current_round > self.max_qualification_rounds:
                self.is_tournament_phase = True
                print("--- КВАЛИФИКАЦИЯ ОКОНЧЕНА! НАЧИНАЕТСЯ ФИНАЛЬНЫЙ ТУРНИР! ---")
        else:
            print(f" Флаг {country_code.upper()} выиграл турнирный раунд!")
            
        self.save_state()

    def reset_tournament(self):
        """Полный сброс всей базы данных турнира."""
        self.qualified_countries = []
        self.current_round = 1
        self.is_tournament_phase = False
        self.save_state()
        print("База данных турнира полностью сброшена.")
