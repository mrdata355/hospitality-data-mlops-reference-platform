# ML Evaluation Limitations

## Purpose

The machine-learning assets in this repository validate implementation behavior, model lifecycle controls, feature contracts, scoring interfaces, and reproducible acceptance gates. They do not establish production business impact.

## Member-risk model

The member-risk outcome is generated deterministically from synthetic member behavior. Several variables that influence the generated outcome are also legitimate training features, including booking recency, stay activity, points utilization, expirations, and service interactions.

The reported ROC AUC therefore demonstrates that the pipeline can:

- build point-in-time feature inputs
- train a reproducible classifier
- preserve the training and serving feature contract
- evaluate and gate a candidate model
- package and serve the accepted artifact

It must not be interpreted as evidence that the same model would achieve comparable discrimination on real hospitality members.

A production evaluation would require an independently observed outcome such as no qualifying booking or stay during a defined future observation window. It would also require multiple historical cutoffs, temporal holdouts, segment analysis, calibration, lift, operational capacity analysis, and post-deployment outcome measurement.

## Resort-week forecast

The forecast is evaluated chronologically against generated resort activity and a 52-week seasonal baseline. WAPE and baseline improvement validate the forecasting workflow and leakage controls, but the values are specific to the synthetic generator.

A production evaluation would additionally require:

- several rolling backtest windows
- forecast-horizon-specific metrics
- resort and market segment metrics
- event and holiday error analysis
- prediction intervals
- capacity and cancellation adjustments
- comparison with the incumbent planning process

## Promotion boundary

Model acceptance in this repository means that a deterministic candidate cleared repository-defined technical gates. It does not constitute business approval, legal approval, fairness approval, or authorization to deploy against real customer data.
