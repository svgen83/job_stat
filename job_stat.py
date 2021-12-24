import os
import requests

from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable


def fetch_statistic_from_hh(vacancy_template, languages, period, region_id):
    statistics = {}
    hh_url = "https://api.hh.ru/vacancies"
    params = {"period": period, "area": region_id}
    hh_description, hh_total = ("items", "found")
    hh_treshold_value = 100
    for language in languages:
        params.update({"text": vacancy_template.format(language)})
        hh_page_records = fetch_records(hh_url,None,params, get_hh_condition)
        if hh_page_records[0]["found"] > hh_treshold_value:
            counted_vacancy = calculate_statistic(hh_page_records,hh_description, hh_total,predict_rub_salary=predict_rub_salary_for_hh)
        if counted_vacancy:
            statistics[language] = counted_vacancy
    return statistics


def fetch_statistic_from_superjob(vacancy_template, languages, period,
                                  region_id):
    statistics = {}
    superjob_url = "https://api.superjob.ru/2.0/oauth2/vacancies/"
    headers = {"X-Api-App-Id": superjob_key}
    params = {
        "catalogues": "Разработка, программирование",
        "period": period,
        "town": superjob_region_id
    }
    sj_description, sj_total = ("objects", "total")
    for language in languages:
        params.update({"keyword": vacancy_template.format(language)})
        sj_page_records = fetch_records(superjob_url, headers, params,get_sj_condition)
        if sj_page_records:
            counted_vacancy = calculate_statistic(sj_page_records,sj_description, sj_total,predict_rub_salary=predict_rub_salary_for_superjob)
            statistics[language] = counted_vacancy
    return statistics


def fetch_records(url, headers, params,get_condition):
    page_records = [] 
    for page in count(0, 1):
        params.update({"page":page})
        page_response = requests.get(
                url,headers=headers, params=params)
        page_response.raise_for_status()
        page_record = page_response.json()
        if get_condition(page_record,page):
            break
        page_records.append(page_record)
    return page_records


def get_sj_condition(page_record, page):
    if page_record["more"] is False:
        return True


def get_hh_condition(page_record, page):
    if page > page_record["pages"]:
        return True  


def get_vacancies(page_records,descripton):
    vacancies = []
    for page_record in page_records:
        vacancy = page_record[descripton]
        vacancies += vacancy
    return vacancies


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


def calculate_statistic(page_records,description, total, predict_rub_salary):
    vacancies_found = page_records[0][total]
    vacancies = get_vacancies(page_records, description)
    rub_salary = predict_rub_salary(vacancies)
    vacancies_processed = len(rub_salary)
    if vacancies_processed:
        sum_salary = sum(rub_salary)
        average_salary = sum_salary // vacancies_processed
        counted_vacancy = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }
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
    

    superjob_region_id = 4
    

    superjob_statistic = fetch_statistic_from_superjob(vacancy_template, languages,
                                                       period,
                                                       superjob_region_id)



    print(output_statistic(superjob_statistic, "superjob"))

    hh_statistic = fetch_statistic_from_hh(vacancy_template, languages, period,
                                           hh_region_id)


    print(output_statistic(hh_statistic, "headhunter"))
