from flask import Flask, render_template, request

app = Flask(__name__)


def add(x, y):
    return x + y


def subtract(x, y):
    return x - y


def multiply(x, y):
    return x * y


def divide(x, y):
    if y == 0:
        return None, "Error! Division by zero."
    return x / y, None


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        try:
            num1 = float(request.form.get("num1"))
            num2 = float(request.form.get("num2"))
            operation = request.form.get("operation")

            if operation == "add":
                result = add(num1, num2)
            elif operation == "subtract":
                result = subtract(num1, num2)
            elif operation == "multiply":
                result = multiply(num1, num2)
            elif operation == "divide":
                result, error = divide(num1, num2)
        except ValueError:
            error = "Invalid input. Please enter numeric values."

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True)
