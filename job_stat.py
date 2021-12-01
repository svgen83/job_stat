import os
import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def fetch_vacancies_from_hh(name_vacancy, languages, period, region_id):
    hh_url = "https://api.hh.ru/vacancies"
    vacancies = {}
    params = {"period": period, "area": region_id}
    for language in languages:
        page_records = []
        page = 0
        pages_number = 1
        params.update({"text": name_vacancy.format(language)})
        while page < pages_number:
            params.update({"page": page})
            page_response = requests.get(
                hh_url, params=params)
            page_response.raise_for_status()
            load_page = page_response.json()
            pages_number = load_page["pages"]
            page += 1
            page_records += load_page["items"]
        vacancies[language] = page_records
    return vacancies


def fetch_vacancies_from_superjob(name_vacancy, languages, period,
                                  region_id):
    vacancy_superjob_url = "https://api.superjob.ru/2.0/oauth2/vacancies/"
    vacancies = {}
    headers = {"X-Api-App-Id": superjob_key}
    params = {
        "catalogues": "Разработка, программирование",
        "period": period,
        "town": superjob_region_id
    }
    for language in languages:
        page_records = []
        page = 0
        more_results = True
        params.update({"keyword": name_vacancy.format(language)})
        while more_results:
            params.update({"page": page})
            page_response = requests.get(
                vacancy_superjob_url,
                headers=headers,
                params=params)
            page_response.raise_for_status()
            load_page = page_response.json()
            more_results = load_page["more"]
            page += 1
            page_records += load_page["objects"]
        vacancies[language] = page_records
    return vacancies


def count_vacancies(vacancies, treshold_value, predict_rub_salary):
    counted_vacancies = {}
    for language, page_records in vacancies.items():
        if len(page_records) > treshold_value:
            vacancies_found = len(page_records)
            rub_salary = predict_rub_salary(page_records)
            vacancies_processed = len(rub_salary)
            sum_salary = sum(rub_salary)
            average_salary = sum_salary // vacancies_processed
            counted_vacancy = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }
            counted_vacancies[language] = counted_vacancy
    return counted_vacancies


def calculate_salary(max_salary, min_salary):
    if max_salary and min_salary:
        calculated_salary = (min_salary + max_salary) // 2
    elif min_salary and not max_salary:
        calculated_salary = int(1.2 * min_salary)
    elif max_salary and not min_salary:
        calculated_salary = int(0.8 * max_salary)
    else:
        calculated_salary = None
    return calculated_salary


def predict_rub_salary_for_hh(vacancies):
    salaries = []
    for vacancy in vacancies:
        if vacancy["salary"] and vacancy["salary"]["currency"] == 'RUR':
            exp_salary = calculate_salary(vacancy["salary"]["to"],
                                          vacancy["salary"]["from"])
            if exp_salary:
                salaries.append(exp_salary)
    return salaries


def predict_rub_salary_for_superjob(vacancies):
    salaries = []
    for vacancy in vacancies:
        if vacancy["currency"] == "rub":
            exp_salary = calculate_salary(vacancy["payment_to"],
                                          vacancy["payment_from"])
            if exp_salary:
                salaries.append(exp_salary)
    return salaries


def estimate_vacancies_and_salaries(counted_vacancies, head_table):
    table_data = [("Язык", "Вакансий найдено", "Вакансий обработано",
                   "Средняя зарплата")]
    for language, vacancy_data in counted_vacancies.items():
        table_data.append((language, vacancy_data["vacancies_found"],
                           vacancy_data["vacancies_processed"],
                           vacancy_data["average_salary"]))
    table = AsciiTable(table_data, head_table)
    return table.table


if __name__ == "__main__":
    load_dotenv()
    superjob_key = os.getenv("SUPERJOB_KEY")

    languages = [
        "C++", "C", "C#", "Python", "Java", "JavaScript", "Ruby", "PHP", "Go",
        "Scala", "Swift", "R", "Kotlin", "1 С"
    ]

    name_vacancy = "программист {}"
    period = 1
    hh_region_id = 1
    hh_treshold_value = 100

    superjob_region_id = 4
    superjob_treshold_value = 10

    superjob_vacancies = fetch_vacancies_from_superjob(name_vacancy, languages,
                                                       period,
                                                       superjob_region_id)

    superjob_statistic = count_vacancies(superjob_vacancies,
                                         superjob_treshold_value,
                                         predict_rub_salary_for_superjob)

    print(estimate_vacancies_and_salaries(superjob_statistic, "superjob"))

    hh_vacancies = fetch_vacancies_from_hh(name_vacancy, languages, period,
                                           hh_region_id)

    hh_statistic = count_vacancies(hh_vacancies, hh_treshold_value,
                                   predict_rub_salary_for_hh)

    print(estimate_vacancies_and_salaries(hh_statistic, "headhunter"))
