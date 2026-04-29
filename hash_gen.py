import streamlit_authenticator as stauth

passwords = ['arturo123', 'carmen123', "admin123"]

# Versión compatible con la última actualización (3.11+)
# Usamos directamente la lógica de hacheo de la clase
hashed_passwords = [stauth.Hasher.hash(pw) for pw in passwords]

print("--- COPIA ESTOS HASHES EN TU CONFIG.YAML ---")
for user, h in zip(['arturo', 'carmen', "admin"], hashed_passwords):
    print(f"\n{user}:")
    print(h)