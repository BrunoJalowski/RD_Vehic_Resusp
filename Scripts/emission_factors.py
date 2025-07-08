import pandas as pd

"EMISSION FACTOR FOR PAVED ROADS"


def emission_paved_roads(pm: float,
                         silt_loading: float,
                         weight: float) -> float:

    """Calculates the particulate matter emission factor for 4 size classes
    (PM2.5, PM10, PM15 and PM30) following EPA's "AP-42: 13.2.1 Paved Roads".

    Args:
        pm (float): particulate matter size class to be estimated
            There are 4 valid options (2.5, 10, 15 and 30)

        silt_loading (float): silt loading on the surface of the road (g/m²)
            Maximum statistical quality within the range of 0,03 - 400 g/m²

        weight (float): average weight (tons) of the vehicles traveling the
        road

    Returns:
        float: emission factor for the chosen particulate matter size class
        (VKT)
    """

    pm_options = {'2.5': 0.15,
                  '10': 0.62,
                  '15': 0.77,
                  '30': 3.23}

    k = pm_options[str(pm)]

    emission_factor = k * pow(silt_loading, 0.912) * pow(weight, 1.021)

    return emission_factor


# -----------------------------------------------------------------------------
"EMISSION FACTOR FOR UNPAVED INDUSTRIAL ROADS"


def emission_unpaved_industrial(pm: float,
                                silt_fraction: float,
                                weight: float) -> float:

    """Estimates unpaved roads' particulate matter emission factor for 3 size
    classes (2.5, 10 and 30) following EPA's "AP-42: 13.2.2 Unpaved Roads".

    Args:
        pm (float): particulate matter size class to be estimated
            There are 3 valid options (2.5, 10 and 30)

        silt_fraction (float): surface material silt content (%)

        weight (float): average weight (tons) of the vehicles traveling the
        road.

    Returns:
        float:  emission factor for the chosen particulate matter size class
        (g/VKT)
    """

    constants = pd.DataFrame(data={'k': [0.15, 1.5, 4.9],
                                   'a': [0.9, 0.9, 0.7],
                                   'b': [0.45, 0.45, 0.45]},
                             index=[2.5, 10, 30]
                             )

    k = constants.loc[pm, 'k']
    a = constants.loc[pm, 'a']
    b = constants.loc[pm, 'b']

    emission_factor = k * pow(silt_fraction / 12, a) * pow(weight / 3, b)

    return emission_factor


# -----------------------------------------------------------------------------
"EMISSION FACTOR FOR UNPAVED OPEN ACCESS PUBLIC ROADS"


def emission_unpaved_public(pm: float,
                            silt_fraction: float,
                            speed: float,
                            moisture: float) -> float:

    """This function takes arguments refering to PM size class, silt fraction
    of the soil, vehicle speed on the road and soil moisture and returns the
    emission factor for this road category.
       The equation and constants used follow EPA AP-42 guidelines for Unpaved
       Open Access Public Roads, according to "AP-42: 13.2.2 Unpaved Roads".

    Args:
        pm (float): particulate matter size class to be estimated
            There are 3 valid options (2.5, 10 and 30)

        silt_fraction (float): surface material silt content (%)

        speed (float): mean vehicle speed (mph)

        moisture (float): surface material moisture content (%)

    Returns:
        float: emission factor for unpaved industrial roads (lb/VMT)
    """

    constants = pd.DataFrame(data={'k': [0.18, 1.8, 6.0],
                                   'a': [1.0, 1.0, 1.0],
                                   'c': [0.2, 0.2, 0.3],
                                   'd': [0.5, 0.5, 0.3],
                                   'wear_emission': [0.00036,
                                                     0.00047,
                                                     0.00047]},
                             index=[2.5, 10, 30]
                             )

    k = constants.loc[pm, 'k']
    a = constants.loc[pm, 'a']
    c = constants.loc[pm, 'c']
    d = constants.loc[pm, 'd']
    wear_emission = constants.loc[pm, 'wear_emission']

    emission_factor = (
        k * (
            (pow(silt_fraction/12, a) * pow(speed/30, d)) /
            pow(moisture/0.5, c)
            ) - wear_emission)

    return emission_factor


# -----------------------------------------------------------------------------
"HOURLY RAINFALL CORRECTION FACTOR FOR PAVED ROADS"


def paved_rainfall_correction(emission_factor: float,
                              rainfall: int,
                              total_period: int) -> float:

    """This function applies a correction factor for PM resuspension emission
    factors based on the proportion of the study that was raining.
        The equation and constants used follow EPA AP-42 guidelines for Paved
       Roads.


    Args:
        emission_factor: calculated emission factor for paved roads (lb/VMT)

        rainfall: total number of hours with over 1 inch of rainfall (hours)

        total_period: total period considered (hours)

    Returns:
        float: corrected emission factor for unpaved roads (lb/VMT)
    """

    corrected_factor = emission_factor * (1 - (1.2 * rainfall / total_period))

    return corrected_factor


# -----------------------------------------------------------------------------
"HOURLY RAINFALL CORRECTION FACTOR FOR UNPAVED ROADS"


def unpaved_rainfall_correction(emission_factor: float,
                                rainfall: int,
                                total_period: int) -> float:
    """This function

       The equation and constants used follow EPA AP-42 guidelines for Unpaved
       Roads.


    Args:
        emission_factor: calculated emission factor for unpaved roads

        rainfall: total number of hours with over 1 inch of rainfall (hours)

        total_period: total period considered (hours)

    Returns:
        float: corrected emission factor for unpaved roads
    """

    corrected_factor = emission_factor * (1 - (rainfall / total_period))

    return corrected_factor


# ----------------------------------------------------------------------------
"lb/VMT to g/VKT CONVERSION"


def lbvmt_to_gvkt(lbvmt: float|int) -> float:
    """
    Converts value in lb/VMT (pounds per vehicle mile traveled) to g/VKT 
    (grams per vehicle kilometer traveled). Commonly applied to emission 
    factor.
    
    Parameters
    ----------
    lbvmt : float | int
        value in lb/VMT

    Returns
    -------
    float
        Value in g/VKT

    """
    return lbvmt * 281.9
