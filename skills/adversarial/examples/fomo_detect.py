"""
Example: FOMO / Panic Detection
================================
Run: python -m skills.adversarial.examples.fomo_detect
"""

from skills.adversarial.sentiment import FOMODetector


def main():
    detector = FOMODetector()

    # Calm market
    calm = detector.detect(
        symbol="BTC/USDT",
        prices=[50000, 50100, 50050, 50120],
        volumes=[100, 110, 105, 108],
    )
    print(f"Calm market: {calm}")

    # Extreme FOMO — parabolic price + volume spike
    fomo = detector.detect(
        symbol="BTC/USDT",
        prices=[50000, 55000, 62000, 75000],
        volumes=[100, 800, 5000, 25000],
    )
    print(f"FOMO regime: {fomo}")

    # Panic — crash with volume spike
    panic = detector.detect(
        symbol="BTC/USDT",
        prices=[75000, 70000, 60000, 45000],
        volumes=[100, 3000, 12000, 40000],
    )
    print(f"Panic regime: {panic}")


if __name__ == "__main__":
    main()
