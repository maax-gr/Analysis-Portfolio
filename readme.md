# Analysis Portfolio

This repository contains data analyses and supporting code.

## Aptamer correlation analysis

The `Aptamer_Correlation/TMR.ipynb` notebook colors a structure of the TMR-3 aptamer structure bound to the ligand 5-TAMRA by normalized RMSF (root mean square fluctuations) from a bundle of structures that resulted from a fit to experimental orientation-selective PELDOR data (structure bundle and exp. data not in repo). Ith then plots pairwise correlations of the distances between the three spin-labels attached to position C12, C30 and C47. It displays linear fits and R² values, using finite conformer rows from `Aptamer_Correlation/Data/Fit_wTMR_SpinLabelDistances.csv`.

The notebook also uses a representative structure from the fit(`Fit_wTMR_reference_frame.pdb`) and normalized RMSF data (`Fit_wTMR_RMSF_normalized.txt`) in the same `Data` folder. Open the notebook with `Aptamer_Correlation` as the working directory and run its code cells from top to bottom.

## RNA11 with Cm spin-label example

`RNA_DNA_structural_data/RNA11_wCm_data_preparation.ipynb` prepares the RNA11 with Cm spin-label example data. It marks omitted rows and `----` values with `99.99`, loads the processed data with `dnaMD`, writes parameter arrays to text files, and creates initial twist-stretch plots. Run it from the repository root. Input, processed, and output filenames use the `RNA11_Cm_tip3p` naming convention.

Install its Python dependencies with `python -m pip install -r RNA_DNA_structural_data/RNA11_wCm_requirements.txt`. See [RNA_DNA_structural_data/README.md](./RNA_DNA_structural_data/README.md) for details.