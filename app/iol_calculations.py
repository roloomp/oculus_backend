from typing import Dict, Optional


class IOLCalculator:
    @staticmethod
    def srk_t(axial_length: float, k1: float, k2: float,
              acd: Optional[float] = None, a_constant: float = 118.5) -> float:
        """
        SRK/T formula. Suitable for most eye lengths.
        acd is accepted but not used (kept for uniform interface).
        """
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

    @staticmethod
    def holladay(axial_length: float, k1: float, k2: float,
                 acd: float, surgeon_factor: float = 1.5) -> float:
        """
        Holladay 1 formula. Best for eyes with average axial length (23–26 mm).
        Requires measured ACD.
        """
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

        term1 = 1336 / (L - ELP - 0.05)
        term2 = K / (1 - 0.012 * K)
        P = term1 - term2

        if not (5 <= P <= 35):
            raise ValueError(
                f"Результат Holladay ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )

        return round(P, 2)

    @staticmethod
    def haigis(axial_length: float, k1: float, k2: float, acd: float,
               a0: float = 1.83, a1: float = 0.4, a2: float = 0.1) -> float:
        """
        Haigis formula. Most accurate for short eyes (< 22 mm).
        Requires measured ACD.
        """
        L = float(axial_length)
        k1_f = float(k1)
        k2_f = float(k2)
        acd_f = float(acd)

        K = (k1_f + k2_f) / 2
        ELP = float(a0) + float(a1) * acd_f + float(a2) * L
        ELP = max(3.0, min(6.0, ELP))

        term1 = 1336 / (L - ELP)
        term2 = K / (1 - 0.012 * K)
        P = term1 - term2

        if not (5 <= P <= 35):
            raise ValueError(
                f"Результат Haigis ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )

        return round(P, 2)

    @staticmethod
    def barrett(axial_length: float, k1: float, k2: float,
                acd: float, lens_factor: float = 1.0) -> float:
        """
        Barrett Universal II approximation.
        Best overall accuracy across the full range of eye lengths.
        """
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

        if not (5 <= P <= 35):
            raise ValueError(
                f"Результат Barrett ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )

        return round(P, 2)

    @staticmethod
    def hoffer_q(axial_length: float, k1: float, k2: float,
                 acd: float, pACD: float = 5.41) -> float:
        """
        Hoffer Q formula. Particularly accurate for short eyes (< 22 mm).
        pACD is the personalized ACD constant (default 5.41).
        Requires measured ACD.
        """
        L = float(axial_length)
        k1_f = float(k1)
        k2_f = float(k2)
        acd_f = float(acd)
        pACD_f = float(pACD)

        K = (k1_f + k2_f) / 2

        # Hoffer Q ELP estimation
        import math
        tan_K = math.tan(math.radians(K))
        ELP = pACD_f + 0.3 * (L - 23.5) + (tan_K ** 2) * 0.1 + 0.1 * (acd_f - 3.5)
        ELP = max(2.5, min(7.0, ELP))

        term1 = 1336 / (L - ELP)
        term2 = K / (1 - 0.012 * K)
        P = term1 - term2

        if not (5 <= P <= 35):
            raise ValueError(
                f"Результат Hoffer Q ({P:.2f} D) вне допустимого диапазона 5–35 D. "
                "Проверьте входные данные."
            )

        return round(P, 2)

    @staticmethod
    def calculate_all(axial_length: float, k1: float, k2: float, acd: float) -> Dict[str, float]:
        """
        Run all five formulas. Each raises ValueError on bad input rather than
        silently returning a fallback value.
        """
        results = {}
        formulas = {
            'srk_t': lambda: IOLCalculator.srk_t(axial_length, k1, k2, acd),
            'holladay': lambda: IOLCalculator.holladay(axial_length, k1, k2, acd),
            'haigis': lambda: IOLCalculator.haigis(axial_length, k1, k2, acd),
            'barrett': lambda: IOLCalculator.barrett(axial_length, k1, k2, acd),
            'hoffer_q': lambda: IOLCalculator.hoffer_q(axial_length, k1, k2, acd),
        }
        errors = {}
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
            'srk_t': lambda: IOLCalculator.srk_t(axial_length, k1, k2, acd),
            'holladay': lambda: IOLCalculator.holladay(axial_length, k1, k2, acd),
            'haigis': lambda: IOLCalculator.haigis(axial_length, k1, k2, acd),
            'barrett': lambda: IOLCalculator.barrett(axial_length, k1, k2, acd),
            'hoffer_q': lambda: IOLCalculator.hoffer_q(axial_length, k1, k2, acd),
        }
        if formula not in dispatch:
            raise ValueError(
                f"Неизвестная формула: '{formula}'. "
                f"Допустимые значения: {', '.join(dispatch.keys())}"
            )
        return dispatch[formula]()

    @staticmethod
    def get_recommendation(axial_length: float, k1: float, k2: float, acd: float) -> Dict:
        L = float(axial_length)

        recommendation = {
            'recommended_formula': 'srk_t',
            'reason': 'Стандартная формула SRK/T подходит для большинства случаев',
            'alternatives': ['holladay', 'haigis'],
            'notes': 'Рекомендуется использовать несколько формул и усреднить результат',
        }

        if L < 22.0:
            recommendation.update({
                'recommended_formula': 'haigis',
                'reason': 'Для коротких глаз (длина < 22 мм) Haigis или Hoffer Q дают наиболее точные результаты',
                'alternatives': ['hoffer_q', 'barrett'],
                'notes': 'Избегайте использования SRK/T для очень коротких глаз',
            })
        elif L > 25.0:
            recommendation.update({
                'recommended_formula': 'barrett',
                'reason': 'Для длинных глаз (длина > 25 мм) Barrett Universal II показывает лучшие результаты',
                'alternatives': ['srk_t', 'holladay'],
                'notes': 'Рекомендуется провести несколько измерений для подтверждения',
            })
        else:
            recommendation.update({
                'recommended_formula': 'holladay',
                'reason': 'Для глаз средней длины Holladay обеспечивает хорошую точность',
                'alternatives': ['srk_t', 'haigis', 'barrett'],
                'notes': 'Все формулы должны давать сходные результаты',
            })

        k_avg = (float(k1) + float(k2)) / 2
        if k_avg < 42.0:
            recommendation['notes'] += '. Плоская роговица: проверьте результаты Barrett'
        elif k_avg > 46.0:
            recommendation['notes'] += '. Крутая роговица: обратите внимание на результаты Haigis'

        return recommendation
