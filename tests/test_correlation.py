import pandas as pd
import numpy as np

def test_correlation_matrix_not_empty():
    """
    Smoke test to verify that correlation calculations produce non-empty results
    """
    # Create small test dataset
    data = {
        'QB_PassYds': [300, 250, 400],
        'WR_RecYds': [100, 80, 150]
    }
    df = pd.DataFrame(data)
    
    # Calculate correlation matrix
    corr_matrix = df.corr()
    
    # Check that matrix is not empty
    assert not corr_matrix.empty
    
    # Check that correlation values are within valid range [-1, 1]
    assert all(-1 <= x <= 1 for x in corr_matrix.values.flatten())
    
    # Check specific correlation exists
    assert not np.isnan(corr_matrix.loc['QB_PassYds', 'WR_RecYds'])