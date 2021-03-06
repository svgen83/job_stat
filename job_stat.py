import os
import requests

from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable


def fetch_statistic_from_hh(vacancy_template, languages):
    statistics = {}
    region_id = 1
    url = "https://api.hh.ru/vacancies"
    params = {"area": region_id}
    min_amount_vacancies = 100

    for language in languages:
        params.update({"text": vacancy_template.format(language)})
        page_records = fetch_records(url, None, params,
                                     get_condition_for_hh_pagination)

        if page_records[0]["found"] >= min_amount_vacancies:
            vacancies_found = page_records[0]["found"]
            statistic_for_language = calculate_statistic(
                page_records,
                vacancies_found,
                predict_rub_salary_for_hh)
        if statistic_for_language:
            statistics[language] = statistic_for_language
    return statistics


def fetch_statistic_from_sj(vacancy_template, languages, superjob_key):
    statistics = {}
    region_id = 4
    url = "https://api.superjob.ru/2.0/oauth2/vacancies/"
    headers = {"X-Api-App-Id": superjob_key}
    params = {
        "catalogues": "Разработка, программирование",
        "town": region_id
    }

    for language in languages:
        params.update({"keyword": vacancy_template.format(language)})
        page_records = fetch_records(url,
                                     headers,
                                     params,
                                     get_condition_for_sj_pagination)

        if page_records:
            vacancies_found = page_records[0]["total"]
            statistic_for_language = calculate_statistic(
                page_records,
                vacancies_found,
                predict_rub_salary_for_sj)
        if statistic_for_language:
            statistics[language] = statistic_for_language
    return statistics


def fetch_records(url, headers, params, get_condition_for_pagination):
    page_records = []
    for page in count(0, 1):
        params.update({"page": page})
        page_response = requests.get(url, headers=headers, params=params)
        page_response.raise_for_status()
        page_record = page_response.json()

        if get_condition_for_pagination(page_record, page):
            break
        page_records.append(page_record)
    return page_records


def get_condition_for_sj_pagination(page_record, *_):
    return not page_record["more"]


def get_condition_for_hh_pagination(page_record, page):
    if page == page_record["pages"] - 1:
        return True


def predict_rub_salary_for_hh(page_records):
    salaries = []
    for page_record in page_records:
        vacancies = page_record["items"]
        for vacancy in vacancies:
            if vacancy["salary"] and vacancy["salary"]["currency"] == 'RUR':
                exp_salary = calculate_salary(
                    vacancy["salary"]["to"],
                    vacancy["salary"]["from"])
                if exp_salary:
                    salaries.append(exp_salary)
    return salaries


def predict_rub_salary_for_sj(page_records):
    salaries = []
    for page_record in page_records:
        vacancies = page_record["objects"]
        for vacancy in vacancies:
            if vacancy["currency"] == "rub":
                exp_salary = calculate_salary(
                    vacancy["payment_to"],
                    vacancy["payment_from"])
                if exp_salary:
                    salaries.append(exp_salary)
    return salaries


def calculate_salary(max_salary, min_salary):
    if max_salary and min_salary:
        return (min_salary + max_salary) // 2
    elif min_salary:
        return int(1.2 * min_salary)
    elif max_salary:
        return int(0.8 * max_salary)


def calculate_statistic(page_records, vacancies_found, predict_rub_salary):
    rub_salary = predict_rub_salary(page_records)
    if len(rub_salary):
        statistic_for_language = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": len(rub_salary),
                "average_salary": sum(rub_salary) // len(rub_salary)
            }
        return statistic_for_language


def output_statistic(statistics, head_table):
    table_contents = [("Язык", "Вакансий найдено", "Вакансий обработано",
                       "Средняя зарплата")]
    for language, vacancy_statistic in statistics.items():
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

    sj_statistic = fetch_statistic_from_sj(
        vacancy_template,
        languages,
        superjob_key)

    print(output_statistic(sj_statistic, "superjob"))

    hh_statistic = fetch_statistic_from_hh(vacancy_template, languages)

    print(output_statistic(hh_statistic, "headhunter"))
