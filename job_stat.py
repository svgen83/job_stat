import os
import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def fetch_vacancies_from_hh(name_vacancy, languages_list, period, region_id):
    hh_url = "https://api.hh.ru/vacancies"
    vacancy_dict = {}
    for language in languages:
        page_records = []
        page = 0
        pages_number = 1
        while page < pages_number:
            params = {
                "text": name_vacancy.format(language),
                "period": period,
                "area": region_id,
                "page": page
            }
            page_response = requests.get(hh_url, params=params)
            page_response.raise_for_status
            pages_number = page_response.json()["pages"]
            page += 1
            page_records += page_response.json()["items"]
        vacancy_dict[language] = page_records
    return vacancy_dict


def fetch_vacancies_from_superjob(name_vacancy, languages_list, period,
                                  region_id):
    vacancy_superjob_url = "https://api.superjob.ru/2.0/oauth2/vacancies/"
    vacancy_dict = {}
    for language in languages:
        page_records = []
        page = 0
        more_results = True
        while more_results is True:
            sj_headers = {"X-Api-App-Id": superjob_key}
            sj_params = {
                "keyword": name_vacancy.format(language),
                "catalogues": "Разработка, программирование",
                "period": period,
                "town": superjob_region_id,
                "page": page
            }
            sj_page_response = requests.get(vacancy_superjob_url,
                                            headers=sj_headers,
                                            params=sj_params)
            sj_page_response.raise_for_status
            more_results = sj_page_response.json()["more"]
            page += 1
            page_records += sj_page_response.json()["objects"]
        vacancy_dict[language] = page_records
    return vacancy_dict


def count_vacancies(vacancy_dict, treshold_value, predict_rub_salary):
    count_dict = {}
    for language, page_records in vacancy_dict.items():
        if len(page_records) > treshold_value:
            vacancies_found = len(page_records)
            vacancies_processed = len((predict_rub_salary(page_records)))
            sum_salary = sum(predict_rub_salary(page_records))
            average_salary = sum_salary // vacancies_processed
            stat_dict = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }
            count_dict[language] = stat_dict
    return count_dict


def predict_rub_salary_for_hh(vacancies_list):
    salary_list = []
    for vacancy in vacancies_list:
        if vacancy["salary"] is not None:
            salary = vacancy["salary"]
            if salary["currency"] == 'RUR':
                min_salary, max_salary = salary["from"], salary["to"]
                if min_salary is None and max_salary is not None:
                    exp_salary = int(0.8 * max_salary)
                elif min_salary is not None and max_salary is None:
                    exp_salary = int(1.2 * min_salary)
                elif min_salary is not None and max_salary is not None:
                    exp_salary = (min_salary + max_salary) // 2
                else:
                    pass
                salary_list.append(exp_salary)
            else:
                exp_salary = None
    return salary_list


def predict_rub_salary_for_superjob(vacancies_list):
    salary_list = []
    for vacancy in vacancies_list:
        exp_salary = 0
        if vacancy["currency"] == "rub":
            min_salary, max_salary = vacancy["payment_from"], vacancy[
                "payment_to"]
            if min_salary == 0 and max_salary != 0:
                exp_salary = int(0.8 * max_salary)
            elif min_salary != 0 and max_salary == 0:
                exp_salary = int(1.2 * min_salary)
            elif min_salary != 0 and max_salary != 0:
                exp_salary = (min_salary + max_salary) // 2
            else:
                pass  #exp_salary = None
            vac = (exp_salary)
            salary_list.append(vac)
        else:
            pass  #exp_salary = None
    return salary_list


def estimate(stat_dict, head_table):
    table_data = [("Язык", "Вакансий найдено", "Вакансий обработано",
                   "Средняя зарплата")]
    for key, value in stat_dict.items():
        table_data.append(
            (key, value["vacancies_found"], value["vacancies_processed"],
             value["average_salary"]))
    table = AsciiTable(table_data, head_table)
    return table.table


if __name__ == "__main__":
    load_dotenv()
    superjob_key = os.getenv("SUPERJOB_KEY")

    languages = ["C++", "C", "C#", "Python", "Java", "JavaScript", "Ruby", "PHP", "Go",
    "Scala", "Swift", "R", "Kotlin", "1 С"]

    name_vacancy = "программист {}"
    period = 5
    hh_region_id = 1
    hh_treshold_value = 100
    
    superjob_region_id = 4
    superjob_treshold_value = 10
    
    superjob_vacancies = fetch_vacancies_from_superjob(name_vacancy, languages,
                                                   period, superjob_region_id)

    superjob_statistic = count_vacancies(superjob_vacancies,
                                     superjob_treshold_value,
                                     predict_rub_salary_for_superjob)

    print(estimate(superjob_statistic, "superjob"))

    hh_vacancies = fetch_vacancies_from_hh(name_vacancy, languages, period,
                                       hh_region_id)

    hh_statistic = count_vacancies(hh_vacancies, hh_treshold_value,
                               predict_rub_salary_for_hh)

    print(estimate(hh_statistic, "headhunter"))
