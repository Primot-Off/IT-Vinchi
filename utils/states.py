from aiogram.fsm.state import State, StatesGroup

class Questionnaire(StatesGroup):
    name = State()
    age = State()
    github = State()
    about = State()
    languages = State()
    photos = State()

class Menu(StatesGroup):
    main = State()
    view = State()
    profile = State()
    profile_edit = State()
    profile_edit_about = State()
    profile_edit_languages = State()
    profile_edit_photos = State()
    view_likes = State()
    feedback_likes = State()