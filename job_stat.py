import os
import requests

from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable


def fetch_vacancies_from_hh(vacancy_template, languages, period, region_id):
    vacancies = {}
    params = {"period": period, "area": region_id}
    for language in languages:
        params.update({"text": vacancy_template.format(language)})
        vacancies[language] = fetch_vacancy_from_hh(params)
    return vacancies


def fetch_vacancy_from_hh(params):
    hh_url = "https://api.hh.ru/vacancies"
    page_records = []
    page = count(0,1)
    pages_number = 1  
    while next(page) < pages_number:
        params.update({"page": next(page)})
        page_response = requests.get(
                hh_url, params=params)
        page_response.raise_for_status()
        loaded_page = page_response.json()
        pages_number = loaded_page["pages"]
        page_records += loaded_page["items"]
    return page_records

def fetch_vacancies_from_superjob(vacancy_template, languages, period,
                                  region_id):
    vacancies = {}
    
    params = {
        "catalogues": "Разработка, программирование",
        "period": period,
        "town": superjob_region_id
    }
    for language in languages:
        params.update({"keyword": vacancy_template.format(language)})
        vacancies[language] = fetch_vacancy_from_superjob(params)
    return vacancies


def fetch_vacancy_from_superjob(params):
    vacancy_superjob_url = "https://api.superjob.ru/2.0/oauth2/vacancies/"
    headers = {"X-Api-App-Id": superjob_key}
    page_records = []
    page = count(0,1)
    more_results = True
    while more_results:
        params.update({"page": next(page)})
        page_response = requests.get(
        vacancy_superjob_url,
        headers=headers,
        params=params)
        page_response.raise_for_status()
        loaded_page = page_response.json()
        more_results = loaded_page["more"]
        page_records += loaded_page["objects"]
    return page_records


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


def output_statistic(counted_vacancies, head_table):
    table_contents = [("Язык", "Вакансий найдено", "Вакансий обработано",
                   "Средняя зарплата")]
    for language, vacancy_statistic in counted_vacancies.items():
        table_contents.append((language, vacancy_statistic["vacancies_found"],
                           vacancy_statistic["vacancies_processed"],
                           vacancy_statistic["average_salary"]))
    table = AsciiTable(table_contents, head_table)
    return table.table


if __name__ == "__main__":
    load_dotenv()
    superjob_key = os.getenv("SUPERJOB_KEY")

    languages = [
        "C++", "C", "C#", "Python", "Java", "JavaScript", "Ruby", "PHP", "Go",
        "Scala", "Swift", "R", "Kotlin", "1 С"
    ]

    vacancy_template = "программист {}"
    period = 1
    hh_region_id = 1
    hh_treshold_value = 100

    superjob_region_id = 4
    superjob_treshold_value = 10

    superjob_vacancies = fetch_vacancies_from_superjob(vacancy_template, languages,
                                                       period,
                                                       superjob_region_id)

    superjob_statistic = count_vacancies(superjob_vacancies,
                                         superjob_treshold_value,
                                         predict_rub_salary_for_superjob)

    print(output_statistic(superjob_statistic, "superjob"))

    hh_vacancies = fetch_vacancies_from_hh(vacancy_template, languages, period,
                                           hh_region_id)

    hh_statistic = count_vacancies(hh_vacancies, hh_treshold_value,
                                   predict_rub_salary_for_hh)

    print(output_statistic(hh_statistic, "headhunter"))
