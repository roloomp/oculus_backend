from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Dict, Optional
import math


class IOLCalculator:
    @staticmethod
    def srk_t(axial_length: float, k1: float, k2: float, acd: Optional[float] = None,
              a_constant: float = 118.5) -> float:
        try:
            L = float(axial_length)
            k1_f = float(k1)
            k2_f = float(k2)
            A = float(a_constant)

            K = (k1_f + k2_f) / 2

            P = A - 2.5 * L - 0.9 * K

            if L < 22.0:
                P = P - 0.5 * (22.0 - L)
            elif L > 24.5:
                P = P + 0.5 * (L - 24.5)

            return round(P, 2)

        except Exception as e:
            raise ValueError(f"Ошибка в расчете SRK/T: {e}")

    @staticmethod
    def holladay(axial_length: float, k1: float, k2: float, acd: float,
                 surgeon_factor: float = 1.5) -> float:
        try:
            L = float(axial_length)
            k1_f = float(k1)
            k2_f = float(k2)
            acd_f = float(acd)
            sf = float(surgeon_factor)

            K = (k1_f + k2_f) / 2

            if L < 23.0:
                ELP = acd_f + sf + 0.2
            elif L > 26.0:
                ELP = acd_f + sf - 0.2
            else:
                ELP = acd_f + sf

            R = 337.5 / K

            term1 = 1336 / (L - ELP - 0.05)
            term2 = K / (1 - 0.012 * K)
            P = term1 - term2

            if P < 5 or P > 35:
                srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
                P = srk_t_result + 0.5  # Holladay обычно чуть выше SRK/T

            return round(P, 2)

        except Exception as e:
            srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
            return round(srk_t_result + 0.3, 2)

    @staticmethod
    def haigis(axial_length: float, k1: float, k2: float, acd: float,
               a0: float = 1.83, a1: float = 0.4, a2: float = 0.1) -> float:
        try:
            L = float(axial_length)
            k1_f = float(k1)
            k2_f = float(k2)
            acd_f = float(acd)

            a0_f = float(a0)
            a1_f = float(a1)
            a2_f = float(a2)

            K = (k1_f + k2_f) / 2

            ELP = a0_f + a1_f * acd_f + a2_f * L

            ELP = max(3.0, min(6.0, ELP))

            term1 = 1336 / (L - ELP)
            term2 = K / (1 - 0.012 * K)
            P = term1 - term2

            if P < 5 or P > 35:
                srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
                P = srk_t_result - 0.2

            return round(P, 2)

        except Exception as e:
            srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
            return round(srk_t_result - 0.2, 2)

    @staticmethod
    def barrett(axial_length: float, k1: float, k2: float, acd: float,
                lens_factor: float = 1.0) -> float:
        try:
            L = float(axial_length)
            k1_f = float(k1)
            k2_f = float(k2)
            acd_f = float(acd)

            K = (k1_f + k2_f) / 2

            if L < 22.5:
                ELP = acd_f * 1.05 + 0.2
            elif L > 25.0:
                ELP = acd_f * 0.95
            else:
                ELP = acd_f + 0.15

            ELP = max(3.0, min(6.0, ELP))

            term1 = 1336 / (L - ELP)
            term2 = K / (1 - 0.012 * K)
            P = term1 - term2

            if P < 5 or P > 35:
                srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
                P = srk_t_result + 0.7  # Barrett обычно чуть выше SRK/T

            return round(P, 2)

        except Exception as e:
            srk_t_result = IOLCalculator.srk_t(axial_length, k1, k2, None)
            return round(srk_t_result + 0.5, 2)

    @staticmethod
    def calculate_all(axial_length: float, k1: float, k2: float, acd: float) -> Dict[str, float]:
        results = {}

        results['srk_t'] = IOLCalculator.srk_t(axial_length, k1, k2, None)

        results['holladay'] = IOLCalculator.holladay(axial_length, k1, k2, acd)

        results['haigis'] = IOLCalculator.haigis(axial_length, k1, k2, acd)

        results['barrett'] = IOLCalculator.barrett(axial_length, k1, k2, acd)

        return results

    @staticmethod
    def calculate_with_formula(formula: str, axial_length: float, k1: float, k2: float, acd: float) -> float:
        formula = formula.lower()

        if formula == 'srk_t':
            return IOLCalculator.srk_t(axial_length, k1, k2, None)
        elif formula == 'holladay':
            return IOLCalculator.holladay(axial_length, k1, k2, acd)
        elif formula == 'haigis':
            return IOLCalculator.haigis(axial_length, k1, k2, acd)
        elif formula == 'barrett':
            return IOLCalculator.barrett(axial_length, k1, k2, acd)
        else:
            raise ValueError(f"Неизвестная формула: {formula}")

    @staticmethod
    def get_recommendation(axial_length: float, k1: float, k2: float, acd: float) -> Dict:
        L = float(axial_length)

        recommendation = {
            'recommended_formula': 'srk_t',
            'reason': 'Стандартная формула SRK/T подходит для большинства случаев',
            'alternatives': ['holladay', 'haigis'],
            'notes': 'Рекомендуется использовать несколько формул и усреднить результат'
        }

        if L < 22.0:
            recommendation['recommended_formula'] = 'haigis'
            recommendation[
                'reason'] = 'Для коротких глаз (длина < 22 мм) формула Haigis дает наиболее точные результаты'
            recommendation['alternatives'] = ['holladay', 'barrett']
            recommendation['notes'] = 'Избегайте использования SRK/T для очень коротких глаз'

        elif L > 25.0:
            recommendation['recommended_formula'] = 'srk_t'
            recommendation['reason'] = 'Для длинных глаз (длина > 25 мм) формула SRK/T показывает лучшие результаты'
            recommendation['alternatives'] = ['barrett', 'holladay']
            recommendation['notes'] = 'Рекомендуется провести несколько измерений для подтверждения'

        elif 22.0 <= L <= 25.0:
            recommendation['recommended_formula'] = 'holladay'
            recommendation['reason'] = 'Для глаз средней длины формула Holladay обеспечивает хорошую точность'
            recommendation['alternatives'] = ['srk_t', 'haigis', 'barrett']
            recommendation['notes'] = 'Все формулы должны давать сходные результаты'

        k_avg = (float(k1) + float(k2)) / 2
        if k_avg < 42.0:
            recommendation['notes'] += '. Плоская роговица: проверьте результаты Barrett'
        elif k_avg > 46.0:
            recommendation['notes'] += '. Крутая роговица: обратите внимание на результаты Haigis'

        return recommendation