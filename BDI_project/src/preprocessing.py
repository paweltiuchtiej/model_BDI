def serie_mapping(df_surface):
    rzeczne_list = []
    zwietrzelina_list = []
    rzeczne_org_1 = []
    rzeczne_org_2 = []
    rzeczne_org_3 = []

    color_mapping = {
        "1":"#a5d76e",
        "2":"#c49dee",
        "20":"#00c3ff",
        "21":"#ffffaf",
        "3":"#4bff91"
    }

    color_map = {
        "#a5d76e": [],  # gleba
        "#c49dee": [],  # rzeczne spoiste
        "#00c3ff": [],  # rzeczne organiczne
        "#ffffaf": [],  # rzeczne niespoiste
        "#4bff91": []   # skały
    }


    serie_list = df_surface["surface"].unique()

    for seria in serie_list:
        clean_seria = seria.replace("S_top_", "")[:-2]
        print(seria)
        assigned_color = color_mapping.get(clean_seria)
        if assigned_color is None:  # TODO ten if jest tutaj na razie prowizorycznie, to sie zmieni tylko musimy ustalić format tych serii
            clean_seria = clean_seria[:-1]
            assigned_color = color_mapping.get(clean_seria)
        color_map[assigned_color].append(seria)

        if clean_seria in ("2", "21"):
            rzeczne_list.append(seria)
        elif clean_seria in ("3"):
            zwietrzelina_list.append(seria)
        elif seria in ("S_top_2001"):
            rzeczne_org_1.append(seria)        
        elif seria in ("S_top_2002"):
            rzeczne_org_2.append(seria)
        elif seria in ("S_top_20014"):
            rzeczne_org_3.append(seria)       

    # for key in color_map.keys():
    #     print(key, ": ", color_map[key])
    return rzeczne_list, zwietrzelina_list, rzeczne_org_1, rzeczne_org_2, color_map
