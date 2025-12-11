#!/usr/bin/env python3
"""Simple Flask API exposing a stub equation solver."""

from __future__ import annotations

import os
from flask import Flask, jsonify, request
from sympy import symbols, Eq, solve, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import *


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):  # type: ignore[override]
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/solve_equation")
    def solve_equation():
        # Enables implicit multiplication
        transformations = standard_transformations + (implicit_multiplication_application,)
        # Maps the inputs to acceptable sympy format, update as needed
        masterFormatTable: Dict[str, str] = {
            "^": "**",
        }
        equation = (request.args.get("equation") or "").strip()

        for replacement in masterFormatTable.items():
            equation = equation.replace(replacement[0], replacement[1])
        if not equation:
            return jsonify({"error": "Missing 'equation' query parameter"}), 400

        try:
            # Detect variables automatically (letters)
            vars_in_eq = sorted({ch for ch in equation if ch.isalpha()})
            symbols_list = [symbols(v) for v in vars_in_eq]

            if "=" in equation:
                # Solve equation
                left_str, right_str = equation.split("=", 1)
                left_expr = parse_expr(left_str, transformations=transformations)
                right_expr = parse_expr(right_str, transformations=transformations)
                equation_sympy = Eq(left_expr, right_expr)

                solution = solve(equation_sympy, symbols_list[0])
                return jsonify({
                    "variable": vars_in_eq[0],
                    "solution": ", ".join(str(s) for s in solution)
                })
            # if there are vars (Ex: x) in an expression, set equal to zero and solve
            elif len(vars_in_eq) > 0:
                # Solve equation
                left_str = equation
                right_str = "0"

                left_expr = parse_expr(left_str, transformations=transformations)
                right_expr = parse_expr(right_str, transformations=transformations)
                equation_sympy = Eq(left_expr, right_expr)

                solution = solve(equation_sympy, symbols_list[0])
                return jsonify({
                    "variable": vars_in_eq[0],
                    "solution": ", ".join(str(s) for s in solution)
                })

            else:
                # Treat as expression → evaluate/simplify
                expr = parse_expr(equation)
                simplified = expr.simplify()  # or use expr.evalf() for numeric value
                return jsonify({
                    "variable": None,
                    "solution": str(simplified)
                })

        except Exception as e:
            return jsonify({"error": f"Error solving equation: {str(e)}"}), 400
            

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"message": "Equation API. Try /solve?equation=1+1"})

    return app


def run() -> None:
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    run()
