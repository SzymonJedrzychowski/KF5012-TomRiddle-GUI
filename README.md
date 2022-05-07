# API and GUI for the KF5012-TomRiddle project.

# Required libraries:
- PyQt5,
- PIL (Pillow),
- tensorflow (version 2.8),
- numpy (should be included with tensorflow instalation),
- Python (version 3.9.0 or newer).

# Other requirements:
- file model.h5 must be included in the same directory as file main.py,
- it it suggested to use machine with Windows 10, as other systems were not tested.

# What is included in this repository:
- API file (CTCovidDetection.py),
- GUI file (mainScreen.py),
- run file (main.py),
- model.h5 (Tensorflow model trained in Iterative Development),
- models directory (directory of other models in .zip files).

# How to use the program:
- Photos (.jpg and .png) can be imported using Import photos button,
- Results can be predicted by pressing Predict button,
- Prediction can be cancelled by pressing Cancel prediction button (replaces Predict button),
- Files can be searched by names using the search field,
- Data can be exported to .json or .csv file using export option (in menu bar).

# Where to get photos:
- Photos from Iterative Development or Baseline Implementation can be used to test the program.