import numpy as np
import pyvista as pv
import matplotlib.colors as mcolors

# --------------------------------------------------------------------------------
# ----------------------------------- 2D i 3D ------------------------------------
# --------------------------------------------------------------------------------

def build_grid(geo_model, group_idx=0):
    ra = geo_model.solutions.raw_arrays
    rg = geo_model.grid.regular_grid
    nx, ny, nz = rg.resolution
    pts = rg.values

    X = pts[:, 0].reshape((nx, ny, nz), order="F")
    Y = pts[:, 1].reshape((nx, ny, nz), order="F")
    Z = pts[:, 2].reshape((nx, ny, nz), order="F")

    grid = pv.StructuredGrid(X, Y, Z)
    grid["lithology"] = ra.lith_block.reshape((nx, ny, nz), order="F").flatten(order="F")

    for i, sf in enumerate(ra.scalar_field_matrix):
        grid[f"scalar_{i}"] = sf.reshape((nx, ny, nz), order="F").flatten(order="F")

    return grid

def get_colors(geo_model):
    """Zwraca tablicę kolorów RGB dla każdej powierzchni w modelu."""
    return np.array([mcolors.to_rgb(s.color) for s in geo_model.structural_frame.surfaces])

def przekroj_to_polyline(df_przekroj, z=240):
    """Buduje tablice 3D punktów polilinii z DataFrame przekroju."""
    return np.array([[row.x, row.y, z]for row in df_przekroj.itertuples()], dtype=float)

def make_pv_line(polyline):
    """Tworzy obiekt PyVista PolyData reprezentujący polylinię."""

    npts = polyline.shape[0]
    cells = np.hstack([[npts], np.arange(npts)]).astype(np.int64)
    return pv.PolyData(polyline, lines=cells)

def build_curtain(grid, polyline, colors_rgb):
    """Wycina przekrój wzdłuż polilinii i przypisuje mu kolory RGB."""
    curtain = grid.slice_along_line(make_pv_line(polyline))
    lith = curtain["lithology"].astype(int)
    
    basement_id = np.max(lith)
    point_mask = lith != basement_id
    
    curtain_filtered = curtain.extract_points(point_mask, adjacent_cells=True)
    
    if curtain_filtered.n_points == 0:
        return curtain_filtered
    
    lith_filtered = curtain_filtered["lithology"].astype(int)
    lith_ids = np.clip(lith_filtered - 1, 0, len(colors_rgb) - 1)
    curtain_filtered.point_data["rgb"] = colors_rgb[lith_ids]
    
    return curtain_filtered

def scale_geometry(grid, polyline=None, scale_xy=10, scale_z=12):
    """Skaluje grid i opcjonalnie polyline."""
    grid_scaled = grid.scale((scale_xy, scale_xy, scale_z), inplace=False)

    if polyline is not None:
        poly_scaled = polyline.copy()
        poly_scaled[:, 0] *= scale_xy
        poly_scaled[:, 1] *= scale_xy
        poly_scaled[:, 2] *= scale_z
    else:
        poly_scaled = None

    return grid_scaled, poly_scaled

# --------------------------------------------------------------------------------
# ------------------------------------- 3D ---------------------------------------
# --------------------------------------------------------------------------------

def add_borehole_3d(plotter, row, z_min, z_max, scale_xy=10):
    """Rysuje pionową linię otworu z etykietą w przestrzeni 3D."""
    x, y = row["X"] * scale_xy, row["Y"] * scale_xy
    plotter.add_mesh(
        pv.Line(np.array([x, y, z_min]), np.array([x, y, z_max])),
        color="red", line_width=2
    )
    plotter.add_point_labels(
        [np.array([x, y, z_max])], [row["NAZW"]],
        font_size=10, text_color="white", bold=True,
        always_visible=True, show_points=True,
        point_size=10, point_color="red",
        shape_opacity=0.4, render_points_as_spheres=True,
    )

def assign_rgb_to_grid_3d(grid, colors_rgb):
    """Przypisuje kolory RGB do punktów gridu na podstawie pola lithology."""
    lith_ids = np.clip(grid["lithology"].astype(int) - 1, 0, len(colors_rgb) - 1)
    grid.point_data["rgb"] = colors_rgb[lith_ids]
    return grid

def add_surface_points_3d(plotter, df_surface, scale_xy=10, scale_z=20):
    pts = np.column_stack([
        df_surface["X"].values * scale_xy,
        df_surface["Y"].values * scale_xy,
        df_surface["Z"].values * scale_z
    ])

    plotter.add_mesh(
        pv.PolyData(pts),
        color="black",
        point_size=8,
        render_points_as_spheres=True
    )

def add_orientations_3d(plotter, df_orient, scale_xy=10, scale_z=20, factor=20):
    pts = np.column_stack([
        df_orient["X"].values * scale_xy,
        df_orient["Y"].values * scale_xy,
        df_orient["Z"].values * scale_z
    ])

    vectors = np.column_stack([
        df_orient["G_x"].values,
        df_orient["G_y"].values,
        df_orient["G_z"].values
    ])

    # normalizacja (bardzo ważne)
    norms = np.linalg.norm(vectors, axis=1)
    norms[norms == 0] = 1  # zabezpieczenie
    vectors = vectors / norms[:, None]

    poly = pv.PolyData(pts)
    poly["vectors"] = vectors

    glyphs = poly.glyph(
        orient="vectors",
        scale=False,
        factor=factor,
        geom=pv.Arrow()
    )

    plotter.add_mesh(glyphs, color="red")

def plot_model_3d(geo_model, df_przekroje_z_otworami, df_boreholes, nazwa_przekroju=None, z_default=240, scale_xy=10, scale_z=20, df_surface=None, df_orient=None):
    """Rysuje model 3D z przekrojem wzdłuż wybranej polilinii."""
    grid = build_grid(geo_model)
    colors_rgb = get_colors(geo_model)
    grid = assign_rgb_to_grid_3d(grid, colors_rgb)

    if nazwa_przekroju is not None:
        dostepne = df_przekroje_z_otworami["nazwa_przekroju"].unique()
        if nazwa_przekroju not in dostepne:
            raise ValueError(
                f"Nie znaleziono przekroju '{nazwa_przekroju}'. "
                f"Dostępne: {list(dostepne)}"
            )
        df_przekroj = df_przekroje_z_otworami[
            df_przekroje_z_otworami["nazwa_przekroju"] == nazwa_przekroju
        ]
        polyline = przekroj_to_polyline(df_przekroj, z_default)
        grid_exag, polyline_scaled = scale_geometry(grid, polyline, scale_xy, scale_z)
        curtain_3d = build_curtain(grid_exag, polyline_scaled, colors_rgb)
    else:
        grid_exag  = scale_geometry(grid, scale_xy=scale_xy, scale_z=scale_z)[0]
        curtain_3d = None

    pl = pv.Plotter()
    if curtain_3d is not None:
        # Model z przekrojem
        pl.add_mesh(grid_exag, scalars="rgb", rgb=True, opacity=0.15, show_edges=False)
        pl.add_mesh(curtain_3d, scalars="rgb", rgb=True, opacity=1.0, show_edges=False)
    
    else:
        def clip_plane(normal, origin):
            clipped = grid_exag.clip(normal=normal, origin=origin)

            lith_ids = np.clip(clipped["lithology"].astype(int) - 1, 0, len(colors_rgb) - 1)
            rgb_uint8 = (np.clip(colors_rgb[lith_ids], 0, 1) * 255).astype(np.uint8)
            clipped.point_data["rgb"] = rgb_uint8

            output.copy_from(clipped)

        output = grid_exag.clip(normal=(1, 0, 0), origin=grid_exag.center)
        lith_ids0 = np.clip(output["lithology"].astype(int) - 1, 0, len(colors_rgb) - 1)
        output.point_data["rgb"] = (np.clip(colors_rgb[lith_ids0], 0, 1) * 255).astype(np.uint8)

        pl.add_mesh(output, scalars="rgb", rgb=True, opacity=1, show_edges=False)

        pl.add_plane_widget(
            clip_plane,
            normal=(1, 0, 0),
            origin=grid_exag.center,
            normal_rotation=False,
            bounds=grid_exag.bounds
        )

    z_min = grid_exag.bounds[4]
    z_max = grid_exag.bounds[5] + 10
    for _, row in df_boreholes.iterrows():
        add_borehole_3d(pl, row, z_min, z_max, scale_xy)

    pl.show_grid(xtitle="X [m]", ytitle="Y [m]", ztitle="Z [m]", font_size=10)
    # add_surface_points_3d(pl, df_surface, scale_xy, scale_z)
    # add_orientations_3d(pl, df_orient, scale_xy, scale_z)
    pl.show()

# --------------------------------------------------------------------------------
# ------------------------------------- 2D ---------------------------------------
# --------------------------------------------------------------------------------

def chainage_along_polyline(points, polyline):
    """Oblicza odległość wzdłuż polilinii dla każdego punktu (chainage)."""
    seg_vecs = np.diff(polyline, axis=0)
    seg_lens = np.linalg.norm(seg_vecs, axis=1)
    seg_dirs = seg_vecs / seg_lens[:, None]
    cumlen = np.concatenate([[0], np.cumsum(seg_lens)])

    s = np.zeros(len(points))
    for i, pt in enumerate(points):
        best_dist, best_s = np.inf, 0.0
        for j in range(len(seg_dirs)):
            p0, t, L = polyline[j], seg_dirs[j], seg_lens[j]
            proj = np.clip(np.dot(pt - p0, t), 0, L)
            dist = np.linalg.norm(pt - (p0 + proj * t))
            if dist < best_dist:
                best_dist = dist
                best_s = cumlen[j] + proj
        s[i] = best_s
    return s

def transform_curtain_to_2d(curtain, polyline):
    """Rzutuje punkty przekroju na układ 2D (chainage, 0, Z)."""
    pts = curtain.points.copy()
    s_coord = chainage_along_polyline(pts, polyline)
    curtain.points = np.column_stack([s_coord, np.zeros_like(s_coord), pts[:, 2]])
    return curtain

def surface_to_color(surface, color_map):
    for color, surfaces in color_map.items():
        if surface in surfaces:
            return color
    return "#888888"

def get_boreholes_info(df_przekroj, polyline, color_map=None, df_otwory_z_litologia=None):
    otwory, counter = [], 1
    for i, row in enumerate(df_przekroj.itertuples()):
        if np.isnan(row.z):
            continue

        pt_3d = np.array([[polyline[i, 0], polyline[i, 1], polyline[i, 2]]])
        s = chainage_along_polyline(pt_3d, polyline)[0]
        nazwa = row.nazwa_otworu if row.nazwa_otworu else f"Otw_{counter}"
        if not row.nazwa_otworu:
            counter += 1

        otw = {"nazwa": nazwa, "s": s, "z_top": row.z, "z_bottom": row.z - row.glebokosc}

        if color_map is not None and df_otwory_z_litologia is not None:
            df_bh = df_otwory_z_litologia[df_otwory_z_litologia["NAZW"] == nazwa].copy()
            df_bh = df_bh.sort_values("strop_from").reset_index(drop=True)

            layers = []
            for idx in range(len(df_bh)):
                band = df_bh.loc[idx]
                z_top = band["Z_top"]

                if idx + 1 < len(df_bh):
                    z_bottom = df_bh.loc[idx + 1, "Z_top"]
                else:
                    z_bottom = otw["z_bottom"]

                layers.append({
                    "z_top":    z_top,
                    "z_bottom": z_bottom,
                    "strop":    band["strop_from"],
                    "symbol":   band["SYMBOL"],
                    "color":    surface_to_color(band["surface"], color_map),
                })

            otw["layers"] = layers

        otwory.append(otw)

    return otwory

def add_borehole_2d(plotter, otw, offset=0.5):
    s, z_top = otw["s"], otw["z_top"]
    if "layers" in otw:
        label_points = []
        label_texts = []
        all_rects = []
        sep_points = []
        sep_lines = []
        pt_offset = 0

        for band in otw["layers"]:
            bz_top = band["z_top"]
            bz_bot = band["z_bottom"]
            if bz_top == bz_bot:
                continue

            # Prostokąt z litologią
            corners = np.array([
                [s - offset / 2, 0, bz_top],
                [s + offset / 2, 0, bz_top],
                [s + offset / 2, 0, bz_bot],
                [s - offset / 2, 0, bz_bot],
            ])
            rect = pv.PolyData(corners, np.array([4, 0, 1, 2, 3]))
            rect.cell_data["color"] = [mcolors.to_rgb(band["color"])]
            all_rects.append(rect)

            # Horyzontalny separator warstw
            sep_points.extend([
                [s - offset / 2, 0, bz_top],
                [s + offset / 2, 0, bz_top],
            ])
            sep_lines.extend([2, pt_offset, pt_offset + 1])
            pt_offset += 2

            # Symbol po środku warstwy i głębokość
            label_points.append([s + offset / 2 + 1, 0, (bz_top + bz_bot) / 2])
            label_texts.append(band["symbol"])
            label_points.append([s + offset / 2, 0, bz_top])
            label_texts.append(f"{band['strop']:.2f}m")

        for rect in all_rects:
            color = mcolors.to_hex(rect.cell_data["color"][0])
            plotter.add_mesh(rect, color=color, show_edges=False, opacity=1.0)

        if sep_points:
            sep_pd = pv.PolyData(
                np.array(sep_points),
                lines=np.array(sep_lines, dtype=np.int64)
            )
            plotter.add_mesh(sep_pd, color="black", line_width=1.5)

        if label_points:
            plotter.add_point_labels(
                np.array(label_points), label_texts,
                font_size=10, text_color="black", bold=False,
                show_points=False, always_visible=True, shape=None
            )

    # Nazwa otworu nad otworem
    plotter.add_point_labels(
        np.array([[s, 0, z_top + 2]]), [otw["nazwa"]],
        font_size=10, text_color="black", bold=False,
        show_points=False, always_visible=True, shape=None
    )

def get_group_lith_ids(geo_model):
    group_lith_ids = {}
    lith_id = 1

    groups = list(geo_model.structural_frame.structural_groups)
    
    for i, group in enumerate(groups):
        ids = set()
        for el in group.elements:
            ids.add(lith_id)
            lith_id += 1
        group_lith_ids[i] = ids

    last_idx = len(groups) - 1
    group_lith_ids[last_idx].add(lith_id)

    return group_lith_ids

# MAIN

def plot_przekroj_2D(geo_model, df_punkty, color_map=None, df_otwory_z_litologia=None, z_default=240):
    grid = build_grid(geo_model)
    colors_rgb = get_colors(geo_model)
    polyline = przekroj_to_polyline(df_punkty, z_default)

    curtain = build_curtain(grid, polyline, colors_rgb)
    curtain = transform_curtain_to_2d(curtain, polyline)
    otwory = get_boreholes_info(df_punkty, polyline, color_map, df_otwory_z_litologia)

    p = pv.Plotter()
    p.enable_parallel_projection()
    p.view_xz()
    p.add_mesh(curtain, scalars="rgb", rgb=True, interpolate_before_map=False, show_edges=False)

    sfsp = geo_model.solutions.raw_arrays.scalar_field_at_surface_points
    groups = geo_model.structural_frame.structural_groups
    group_lith_ids = get_group_lith_ids(geo_model)

    for i, (group, sf_vals) in enumerate(zip(groups, sfsp)):
        if len(sf_vals) == 0:
            continue
        scalar_key = f"scalar_{i}"
        if scalar_key not in curtain.array_names:
            continue

        lith_ids = group_lith_ids[i]
        
        lith = curtain["lithology"]
        mask = np.zeros(len(lith), dtype=bool)
        for lid in lith_ids:
            mask |= (lith == lid)
        
        if mask.sum() == 0:
            continue

        curtain_masked = curtain.extract_points(mask, adjacent_cells=True)
        

        # if curtain_masked.n_points == 0:
        #     continue
        
        # p.add_mesh(
        #     curtain_masked.contour(
        #         isosurfaces=sf_vals.tolist(),
        #         scalars=scalar_key
        #     ),
        #     color="black",
        #     line_width=1
        # )

        contours = curtain_masked.contour(
            isosurfaces=sf_vals.tolist(),
            scalars=scalar_key
        )

        if contours.n_points == 0:
            continue

        p.add_mesh(
            contours,
            color="black",
            line_width=1
        )

    for otw in otwory:
        add_borehole_2d(p, otw)

    # # Get x_range from boreholes
    # borehole_x_values = [otw["s"] for otw in otwory]
    # x_min = min(borehole_x_values)
    # x_max = max(borehole_x_values)

    # # Round to nearest 5
    # x_min = np.floor(x_min / 5) * 5
    # x_max = np.ceil(x_max / 5) * 5

    # # Get z ranges
    # z_min_data = curtain.bounds[4]
    # z_max = curtain.bounds[5]
    # z_min_visual = z_min_data - 0.2

    # # Number of labels
    # n_xlabels = int((x_max - x_min) / 5) + 1
    # n_zlabels = int((z_max - 0) / 10) + 1  # Start from 0 with step 10

    p.show_bounds(
        xtitle="Distance along profile [m]",
        ztitle="Elevation [m]",
        location="outer",
        font_size=8,
        n_zlabels=10
        # bounds=[x_min, x_max, 0, 0, z_min_visual, z_max],
        # n_xlabels=n_xlabels,
        # n_zlabels=n_zlabels,
    )
    p.reset_camera()
    p.show(interactive=False)