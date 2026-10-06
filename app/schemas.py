from typing import Annotated

from pydantic import BaseModel, Field


class PatientInput(BaseModel):
    diabetes: Annotated[bool, Field(description='Наличие диабета')]
    family_history: Annotated[bool, Field(description='Заболевания в семье')]
    obesity: Annotated[bool, Field(description='Наличие ожирения')]
    alcohol_consumption: Annotated[bool, Field(description='Употребление алкоголя')]
    previous_heart_problems: Annotated[
        bool, Field(description='Проблемы с сердцем ранее')
    ]
    medication_use: Annotated[bool, Field(description='Приём препаратов')]

    diet: Annotated[int, Field(ge=0, le=2, description='Тип диеты')]
    stress_level: Annotated[int, Field(ge=1, le=10, description='Уровень стресса')]
    physical_activity_days_per_week: Annotated[
        int, Field(ge=0, le=7, description='Дней физической активности в неделю')
    ]

    age: Annotated[float, Field(ge=0, le=1, description='Возраст (нормализованный)')]
    cholesterol: Annotated[float, Field(ge=0, le=1, description='Холестерин')]
    heart_rate: Annotated[float, Field(ge=0, le=1, description='Пульс')]
    exercise_hours_per_week: Annotated[
        float, Field(ge=0, le=1, description='Часы упражнений в неделю')
    ]
    sedentary_hours_per_day: Annotated[
        float, Field(ge=0, le=1, description='Часы сидячего образа жизни в день')
    ]
    bmi: Annotated[float, Field(ge=0, le=1, description='Индекс массы тела')]
    triglycerides: Annotated[float, Field(ge=0, le=1, description='Триглицериды')]
    blood_sugar: Annotated[float, Field(ge=0, le=1, description='Уровень сахара в крови')]
    ck_mb: Annotated[float, Field(ge=0, le=1, description='Фермент креатинкиназы')]
    troponin: Annotated[float, Field(ge=0, le=1, description='Уровень тропонина')]
    systolic_blood_pressure: Annotated[
        float, Field(ge=0, le=1, description='Систолическое давление')
    ]
    diastolic_blood_pressure: Annotated[
        float, Field(ge=0, le=1, description='Диастолическое давление')
    ]
    sleep_hours_per_day: Annotated[
        float, Field(ge=0, le=1, description='Часы сна в день')
    ]


class PredictionOutput(BaseModel):
    id: Annotated[int, Field(description='ID записи')]
    prediction: Annotated[
        int, Field(description='Предсказанный класс (0 — низкий риск, 1 — высокий)')
    ]
    probability: Annotated[float, Field(description='Вероятность высокого риска')]


class PredictionRequest(BaseModel):
    patients: Annotated[
        list[PatientInput], Field(description='Список пациентов для предсказания')
    ]


class PredictionResponse(BaseModel):
    predictions: Annotated[
        list[PredictionOutput], Field(description='Список предсказаний')
    ]
