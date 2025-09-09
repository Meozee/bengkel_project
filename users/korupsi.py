def orang_yang_ga_kebagian_uang_karena_dikorupsi(rakyat):
    
    pemberi = set(memberi for memberi, menerima in rakyat)
    
    penerima = set(menerima for memberi, menerima in rakyat)
    
    
    for orang in penerima:
        if orang not in pemberi:
            return orang 

rakyat = [
    ["presiden", "dpr"],
    ["dpr", "gubernur"],
    ["gubernur", "camat"],
    ["camat", "warga_biasa"]
]
#Python ngeluarin slot_0 ke memberi dan slot_1 ke menerima.Makanya dia tahu mana yang siapa.

print(orang_yang_ga_kebagian_uang_karena_dikorupsi(rakyat))

