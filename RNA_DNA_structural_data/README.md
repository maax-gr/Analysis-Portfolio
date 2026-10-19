# RNA11 with Cm spin-label example

`RNA11_wCm_data_preparation.ipynb` prepares the RNA11 with Cm spin-label example data. It adds `99.99` rows where raw frames omit rows, changes `----` values to `99.99`, loads the processed files with `dnaMD`, saves parameter arrays, and makes initial twist-stretch plots.

Run the notebook from the Analysis-Portfolio repository root, with the input data in `MD_data/RNA11_wCm_tip3p/`. Install the notebook dependencies with:

```powershell
python -m pip install -r RNA_DNA_structural_data/RNA11_wCm_requirements.txt
```

The raw inputs use names such as `L-BP_RNA11_Cm_tip3p_raw.dat`. The notebook creates corresponding `_processed.dat` files and `RNA11_Cm_tip3p_*.txt` parameter exports.
