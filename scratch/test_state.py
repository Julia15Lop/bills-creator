import pandas as pd

df_precios = pd.DataFrame({'A': [1.0, 2.0, 3.0], 'B': ['a', 'b', 'c']})
df_mostrar = df_precios.iloc[[1, 2]] # filtered to index 1 and 2

# pos '0' corresponds to index 1, pos '1' corresponds to index 2
state = {
    'edited_rows': {'0': {'A': 10.0}},
    'added_rows': [{'A': 4.0, 'B': 'd'}],
    'deleted_rows': [1] # deletes position 1, which is index 2
}

# 1. Apply edited rows
for pos_str, changes in state.get('edited_rows', {}).items():
    pos = int(pos_str)
    actual_idx = df_mostrar.index[pos]
    for col, val in changes.items():
        df_precios.at[actual_idx, col] = val

# 2. Apply deleted rows
deleted_positions = state.get('deleted_rows', [])
if deleted_positions:
    indices_to_drop = [df_mostrar.index[pos] for pos in deleted_positions]
    df_precios = df_precios.drop(index=indices_to_drop)

# 3. Apply added rows
added_rows = state.get('added_rows', [])
if added_rows:
    df_added = pd.DataFrame(added_rows)
    df_precios = pd.concat([df_precios, df_added], ignore_index=True)

print("Resulting DataFrame:")
print(df_precios)
