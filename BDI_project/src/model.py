import gempy as gp
import gempy_viewer as gpv
import torch

def model(df_surface, df_orient, zwietrzelina_list, rzeczne_list, rzeczne_org_1, rzeczne_org_2, color_map):
    surface_points_table: gp.data.SurfacePointsTable = gp.data.SurfacePointsTable.from_arrays(
        x=df_surface['X'].values,
        y=df_surface['Y'].values,
        z=df_surface['Z'].values,
        names=df_surface['surface'].values.astype(str)
    )

    orientations_table: gp.data.OrientationsTable = gp.data.OrientationsTable.from_arrays(
        x=df_orient['X'].values,
        y=df_orient['Y'].values,
        z=df_orient['Z'].values,
        G_x=df_orient['G_x'].values,
        G_y=df_orient['G_y'].values,
        G_z=df_orient['G_z'].values,
        names=df_orient['surface'].values.astype(str)
    )

    structural_frame: gp.data.StructuralFrame = gp.data.StructuralFrame.from_data_tables(
        surface_points=surface_points_table,
        orientations=orientations_table
    )

    geo_model: gp.data.GeoModel = gp.create_geomodel(
        project_name='BDI',
        extent=[
            5529959.407 - 5,   # trzeba dodawać lekki margines z każdej strony żeby otwory na skraju miały wygenerowany model
            5530045.859 + 5,
            7416020.81  - 5,
            7416085.434 + 5,
            213, 234
        ],
        refinement=4,
        structural_frame=structural_frame
    )

    gp.add_structural_group(
        model=geo_model,
        group_index=0,
        structural_group_name="zwietrzelina",
        structural_relation=gp.data.StackRelationType.ERODE,
        elements=[geo_model.structural_frame.get_element_by_name(name) for name in zwietrzelina_list]
    )

    gp.add_structural_group(
        model=geo_model,
        group_index=3,
        structural_group_name="rzeczne1",
        structural_relation=gp.data.StackRelationType.ERODE,
        elements=[geo_model.structural_frame.get_element_by_name(name) for name in rzeczne_list]
    )

    gp.add_structural_group(
        model=geo_model,
        group_index=1,
        structural_group_name="rzeczne2",
        structural_relation=gp.data.StackRelationType.ERODE,
        elements=[geo_model.structural_frame.get_element_by_name(name) for name in rzeczne_org_1]
    )

    gp.add_structural_group(
        model=geo_model,
        group_index=2,
        structural_group_name="rzeczne3",
        structural_relation=gp.data.StackRelationType.ERODE,
        elements=[geo_model.structural_frame.get_element_by_name(name) for name in rzeczne_org_2]
    )

    # gp.add_structural_group(
    #     model=geo_model,
    #     group_index=3,
    #     structural_group_name="rzeczne4",
    #     structural_relation=gp.data.StackRelationType.ERODE,
    #     elements=[geo_model.structural_frame.get_element_by_name(name) for name in rzeczne_org_3]
    # )

    gp.add_structural_group(
        model=geo_model,
        group_index=4,
        structural_group_name="gleba",
        structural_relation=gp.data.StackRelationType.ONLAP,
        elements=[
            geo_model.structural_frame.get_element_by_name("S_top_101")
        ]
    )

    gp.remove_structural_group_by_name(model=geo_model, group_name="default_formation")

    for color, names in color_map.items():
        for name in names:
            geo_model.structural_frame.get_element_by_name(name).color = color
    geo_model.structural_frame.basement_color = "#ffffff"

    geo_model.grid.rescale_factor = [1, 1, 1]

    print(torch.cuda.current_device())
    print(torch.cuda.get_device_name(0))
    USE_GPU = torch.cuda.is_available()
    print("CUDA available:", USE_GPU)
    print(torch.get_default_dtype())
    torch.set_default_dtype(torch.float32)

    geo_model.interpolation_options.kernel_options.use_gpu = True
    # geo_model.interpolation_options.evaluation_options.verbose = True

    with torch.no_grad():
        gp.compute_model(
            geo_model,
            engine_config=gp.data.GemPyEngineConfig(backend=gp.data.AvailableBackends.PYTORCH,use_gpu=True)
        )
    
    return geo_model