import os
import requests

from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable


def fetch_statistic_from_hh(vacancy_template, languages, period, region_id):
    hh_vacancies = {}
    params = {"period": period, "area": region_id}
    for language in languages:
        params.update({"text": vacancy_template.format(language)})
        hh_page_records = fetch_records_from_hh(params)
        counted_vacancy = hh_calculate(hh_page_records)
        if counted_vacancy:
            hh_vacancies[language] = counted_vacancy
    return hh_vacancies


def fetch_records_from_hh(params):
    hh_url = "https://api.hh.ru/vacancies"
    page_records = [] 
    for page in count(0, 1):
        params.update({"page":page})
        page_response = requests.get(
                hh_url, params=params)
        page_response.raise_for_status()
        page_record = page_response.json()
        if page > page_record["pages"]:
            break
        page_records.append(page_record)
    return page_records


def get_vacancies(hh_page_records):
    vacancies = []
    for hh_page_record in hh_page_records:
        vacancy = hh_page_record["items"]
        vacancies += vacancy
    return vacancies


def predict_rub_salary_for_hh(qacancies):
    salaries = []
    for qacancy in qacancies:
        if qacancy["salary"] and qacancy["salary"]["currency"] == 'RUR':
            exp_salary = calculate_salary(qacancy["salary"]["to"],
                                          qacancy["salary"]["from"])
            if exp_salary:
                salaries.append(exp_salary)
    return salaries

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

def hh_calculate(hh_page_records):
    vacancies_found = hh_page_records[0]["found"]    
    qacancies = get_vacancies(hh_page_records)
    rub_salary = predict_rub_salary_for_hh(qacancies)
    vacancies_processed = len(rub_salary)
    sum_salary = sum(rub_salary)
    average_salary = sum_salary // vacancies_processed
    counted_vacancy = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }
    if vacancies_found >= 100 and average_salary > 0:
        return counted_vacancy


def output_statistic(counted_vacancies, head_table):
    table_contents = [("Язык", "Вакансий найдено", "Вакансий обработано",
                   "Средняя зарплата")]
    for language, vacancy_statistic in counted_vacancies.items():
        table_contents.append((language, vacancy_statistic["vacancies_found"],
                           vacancy_statistic["vacancies_processed"],
                           vacancy_statistic["average_salary"]))
    table = AsciiTable(table_contents, head_table)
    return table.table


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
    for page in count(0, 1):
        params.update({"page":page})
        page_response = requests.get(
        vacancy_superjob_url,
        headers=headers,
        params=params)
        page_response.raise_for_status()
        loaded_page = page_response.json()
        if loaded_page["more"] is False:
            break
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


def predict_rub_salary_for_superjob(vacancies):
    salaries = []
    for vacancy in vacancies:
        if vacancy["currency"] == "rub":
            exp_salary = calculate_salary(vacancy["payment_to"],
                                          vacancy["payment_from"])
            if exp_salary:
                salaries.append(exp_salary)
    return salaries





if __name__ == "__main__":
    load_dotenv()
    superjob_key = os.getenv("SUPERJOB_KEY")

    languages1 = [
        "C++", "C", "C#", "Python", "Java", "JavaScript", "Ruby", "PHP", "Go",
        "Scala", "Swift", "R", "Kotlin", "1 С"
    ]
    languages = ["Swift", "R", "Kotlin", "1 С"]

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

    hh_statistic = fetch_statistic_from_hh(vacancy_template, languages, period,
                                           hh_region_id)


    print(output_statistic(hh_statistic, "headhunter"))
