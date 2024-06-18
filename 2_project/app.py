from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
from datetime import datetime

app = FastAPI()

# 세금 데이터 로드
file_path = 'tax.xlsx'
tax_data = pd.read_excel(file_path, skiprows=5)
tax_data.columns = ['이상', '미만', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
tax_data['이상'] = pd.to_numeric(tax_data['이상'], errors='coerce')
tax_data['미만'] = pd.to_numeric(tax_data['미만'], errors='coerce')

# 소득세 계산 함수
def calculate_income_tax(salary, dependents):
    if salary <= 1060000:
        return 0

    if dependents > 11:
        dependents = 11

    salary_range = tax_data[(tax_data['이상'] <= salary) & (tax_data['미만'] > salary)]
    base_tax = tax_data[(tax_data['이상'] <= 10000000) & (tax_data['미만'] > 10000000)][dependents].values[0]

    if 10000000 < salary <= 14000000:
        excess_amount = salary - 10000000
        additional_tax = (excess_amount * 0.98) * 0.35 + 25000
        return base_tax + additional_tax
    elif 14000000 < salary <= 28000000:
        excess_amount = salary - 14000000
        additional_tax = (excess_amount * 0.98) * 0.38 + 1397000
        return base_tax + additional_tax
    elif 28000000 < salary <= 30000000:
        excess_amount = salary - 28000000
        additional_tax = (excess_amount * 0.98) * 0.40 + 6610600
        return base_tax + additional_tax
    elif 30000000 < salary <= 45000000:
        excess_amount = salary - 30000000
        additional_tax = (excess_amount * 0.98) * 0.40 + 7394600
        return base_tax + additional_tax
    elif 45000000 < salary <= 87000000:
        excess_amount = salary - 45000000
        additional_tax = (excess_amount * 0.98) * 0.42 + 13394600
        return base_tax + additional_tax
    elif salary > 87000000:
        excess_amount = salary - 87000000
        additional_tax = (excess_amount * 0.98) * 0.45 + 31034600
        return base_tax + additional_tax

    if salary_range.empty:
        return 0
        
    income_tax = float(salary_range[dependents].values[0])
    return income_tax

def round_ten(value):
    return int(value // 10 * 10)

@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open("static/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.post("/calculate", response_class=JSONResponse)
async def calculate(salary: int = Form(0), tax_Free: int = Form(0), dependents: int = Form(1)):
    if dependents > 11:
        dependents = 11
    
    taxable_salary = salary - tax_Free
    national_pension = round_ten(taxable_salary * 0.045)
    if national_pension > 265500:
        national_pension = 265500
    health_insurance = round_ten(taxable_salary * 0.03545)
    long_term_care_insurance = round_ten(health_insurance * 0.1295)
    employment_insurance = round_ten(taxable_salary * 0.009)
    income_tax = calculate_income_tax(taxable_salary, dependents)
    local_income_tax = round_ten(income_tax * 0.1)
    total_salary = taxable_salary - (national_pension + health_insurance + long_term_care_insurance + employment_insurance + income_tax + local_income_tax) + tax_Free

    return {
        "national_pension": f"{int(national_pension):,} 원",
        "health_insurance": f"{int(health_insurance):,} 원",
        "long_term_care_insurance": f"{int(long_term_care_insurance):,} 원",
        "employment_insurance": f"{int(employment_insurance):,} 원",
        "income_tax": f"{int(income_tax):,} 원",
        "local_income_tax": f"{int(local_income_tax):,} 원",
        "total_salary": f"{int(total_salary):,} 원"
    }

@app.get("/tax.xlsx")
async def download_tax():
    file_path = 'tax.xlsx'
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="tax.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 정적 파일 제공
app.mount("/static", StaticFiles(directory="static"), name="static")

# app.mount("/static", StaticFiles(directory="static"), name="static")는 FastAPI 애플리케이션에 정적 파일을 제공하기 위한 설정입니다. 이 설정은 FastAPI가 특정 경로에서 정적 파일(HTML, CSS, JavaScript, 이미지 등)을 제공할 수 있도록 도와줍니다. 이 코드는 다음과 같은 역할을 합니다:

# 경로 설정: /static 경로를 설정하여, 클라이언트가 이 경로를 통해 정적 파일에 접근할 수 있게 합니다.
# 디렉토리 지정: directory="static"는 FastAPI에 정적 파일이 저장된 디렉토리를 지정합니다. 이 경우 static 디렉토리 내의 파일들이 제공됩니다.
# 이름 지정: name="static"는 이 경로에 대한 이름을 설정합니다. 이는 디버깅이나 로그에서 이 경로를 식별할 때 유용할 수 있습니다.
# 이 설정을 통해 FastAPI 애플리케이션은 /static 경로로 들어오는 요청을 처리하여, static 디렉토리 내의 정적 파일을 클라이언트에 제공할 수 있습니다. 예를 들어, 클라이언트가 http://localhost:5500/static/index.html로 요청하면, FastAPI는 static 디렉토리 내의 index.html 파일을 찾아 클라이언트에 반환합니다.

# 이 설정이 없으면 FastAPI는 동적 요청만 처리할 수 있고, 정적 파일을 직접 제공하지 않습니다.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5500)
