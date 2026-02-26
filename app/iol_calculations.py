import math
from typing import Dict, Optional


class IOLCalculator:
    _N = 1336.0

    @staticmethod
    def _vergence(L: float, K: float, ELP: float) -> float:
        n = IOLCalculator._N
        return n / (L - ELP) - K / (1 - (ELP / n) * K)

    @staticmethod
    def _corneal_geometry(AL: float, K: float):
        R = 337.5 / K
        Cw = -5.41 + 0.58412 * AL + 0.098 * K   # corneal diameter
        Cw = max(0.01, min(Cw, 2.0 * R - 0.01))  # must satisfy 0 < Cw < 2R
        H = R - math.sqrt(R ** 2 - (Cw / 2) ** 2)
        return R, H

    # ── Public formula methods ────────────────────────────────────────────────

    @staticmethod
    def srk_t(axial_length: float, k1: float, k2: float,
               acd: Optional[float] = None,
               a_constant: float = 118.5) -> float:
        L = float(axial_length)
        K = (float(k1) + float(k2)) / 2
        A = float(a_constant)

        P = A - 2.5 * L - 0.9 * K

        if L < 22.0:
            P -= 0.5 * (22.0 - L)
        elif L > 24.5:
            P += 0.5 * (L - 24.5)

        return round(P, 2)

    @staticmethod
    def holladay(axial_length: float, k1: float, k2: float,
                 acd: float,
                 surgeon_factor: float = 1.5) -> float:

        L = float(axial_length)
        K = (float(k1) + float(k2)) / 2
        SF = float(surgeon_factor)

        _, H = IOLCalculator._corneal_geometry(L, K)
        # Predicted postoperative ACD = 0.56 + corneal height + surgeon factor
        ELP = 0.56 + H + SF
        ELP = max(2.5, min(7.5, ELP))

        P = IOLCalculator._vergence(L, K, ELP)

        if not (5.0 <= P <= 35.0):
            raise ValueError(
                f"Результат Holladay ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )
        return round(P, 2)

    @staticmethod
    def haigis(axial_length: float, k1: float, k2: float, acd: float,
               a0: float = 1.36,
               a1: float = 0.40,
               a2: float = 0.10) -> float:

        L = float(axial_length)
        K = (float(k1) + float(k2)) / 2
        ACD = float(acd)

        ELP = float(a0) + float(a1) * ACD + float(a2) * L
        ELP = max(3.0, min(6.0, ELP))

        P = IOLCalculator._vergence(L, K, ELP)

        if not (5.0 <= P <= 35.0):
            raise ValueError(
                f"Результат Haigis ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )
        return round(P, 2)

    @staticmethod
    def hoffer_q(axial_length: float, k1: float, k2: float,
                 acd: float,
                 pACD: float = 5.41) -> float:

        L = float(axial_length)
        K = (float(k1) + float(k2)) / 2
        pACD_f = float(pACD)

        tanK2 = math.tan(math.radians(K)) ** 2

        if L <= 23.0:
            ELP = pACD_f - 0.5642 * (23.5 - L) ** 0.4968 + tanK2 * 0.1
        else:
            ELP = pACD_f + 0.3 * (L - 23.5) + tanK2 * 0.1

        ELP = max(2.5, min(7.0, ELP))

        P = IOLCalculator._vergence(L, K, ELP)

        if not (5.0 <= P <= 35.0):
            raise ValueError(
                f"Результат Hoffer Q ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )
        return round(P, 2)

    @staticmethod
    def barrett(axial_length: float, k1: float, k2: float,
                acd: float,
                lens_factor: float = 1.93) -> float:

        L = float(axial_length)
        K = (float(k1) + float(k2)) / 2
        LF = float(lens_factor)

        # Optical axial length (retinal thickness correction)
        RT = 0.65696 - 0.02029 * L
        L_opt = L - RT

        # Corneal height from optical AL
        _, H = IOLCalculator._corneal_geometry(L_opt, K)
        ELP = 0.56 + H + LF
        ELP = max(3.0, min(7.0, ELP))

        # Barrett uses optical AL in the vergence equation
        P = IOLCalculator._vergence(L_opt, K, ELP)

        if not (5.0 <= P <= 35.0):
            raise ValueError(
                f"Результат Barrett ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )
        return round(P, 2)

    # ── Batch helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def calculate_all(axial_length: float, k1: float, k2: float,
                      acd: float) -> Dict:
        """Run all five formulas and return results + any per-formula errors."""
        formulas = {
            'srk_t':    lambda: IOLCalculator.srk_t(axial_length, k1, k2, acd),
            'holladay': lambda: IOLCalculator.holladay(axial_length, k1, k2, acd),
            'haigis':   lambda: IOLCalculator.haigis(axial_length, k1, k2, acd),
            'barrett':  lambda: IOLCalculator.barrett(axial_length, k1, k2, acd),
            'hoffer_q': lambda: IOLCalculator.hoffer_q(axial_length, k1, k2, acd),
        }
        results: Dict = {}
        errors: Dict = {}
        for name, fn in formulas.items():
            try:
                results[name] = fn()
            except ValueError as e:
                errors[name] = str(e)

        if errors:
            results['errors'] = errors
        return results

    @staticmethod
    def calculate_with_formula(formula: str, axial_length: float, k1: float,
                                k2: float, acd: float) -> float:
        formula = formula.lower()
        dispatch = {
            'srk_t':    lambda: IOLCalculator.srk_t(axial_length, k1, k2, acd),
            'holladay': lambda: IOLCalculator.holladay(axial_length, k1, k2, acd),
            'haigis':   lambda: IOLCalculator.haigis(axial_length, k1, k2, acd),
            'barrett':  lambda: IOLCalculator.barrett(axial_length, k1, k2, acd),
            'hoffer_q': lambda: IOLCalculator.hoffer_q(axial_length, k1, k2, acd),
        }
        if formula not in dispatch:
            raise ValueError(
                f"Неизвестная формула: '{formula}'. "
                f"Допустимые значения: {', '.join(dispatch.keys())}"
            )
        return dispatch[formula]()

    @staticmethod
    def get_recommendation(axial_length: float, k1: float, k2: float,
                           acd: float) -> Dict:
        L = float(axial_length)
        k_avg = (float(k1) + float(k2)) / 2

        if L < 22.0:
            rec = {
                'recommended_formula': 'haigis',
                'reason': 'Для коротких глаз (< 22 мм) Haigis и Hoffer Q дают наиболее точные результаты',
                'alternatives': ['hoffer_q', 'barrett'],
                'notes': 'Избегайте SRK/T для очень коротких глаз',
            }
        elif L > 25.0:
            rec = {
                'recommended_formula': 'barrett',
                'reason': 'Для длинных глаз (> 25 мм) Barrett Universal II показывает лучшие результаты',
                'alternatives': ['srk_t', 'holladay'],
                'notes': 'Рекомендуется провести несколько измерений для подтверждения',
            }
        else:
            rec = {
                'recommended_formula': 'holladay',
                'reason': 'Для глаз средней длины Holladay 1 обеспечивает хорошую точность',
                'alternatives': ['srk_t', 'haigis', 'barrett'],
                'notes': 'Все формулы должны давать схожие результаты',
            }

        if k_avg < 42.0:
            rec['notes'] += '. Плоская роговица: проверьте результаты Barrett'
        elif k_avg > 46.0:
            rec['notes'] += '. Крутая роговица: обратите внимание на Haigis'

        return rec
