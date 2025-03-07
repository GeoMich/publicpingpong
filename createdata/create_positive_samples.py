from re import X
from typing import List
import numpy as np
import math
import pandas as pd
import os.path
from PIL import Image
import matplotlib.pyplot as plt

from typing import List, Dict, Tuple
import pickle


def tile2long(x, z):
    return x / math.pow(2, z) * 360 - 180


def tile2lat(y, z):
    n = math.pi - 2 * math.pi * y / math.pow(2, z)
    return 180 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


def long2tile(lon, zoom):
    return math.floor((lon + 180) / 360 * math.pow(2, zoom))


def lat2tile(lat, zoom):
    return math.floor(
        (
            1
            - math.log(
                math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)
            )
            / math.pi
        )
        / 2
        * math.pow(2, zoom)
    )


def plot_single_image(image_array: np.ndarray, figsize=(100, 150)) -> None:
    """Plot single images

    Args:
        image_array (np.ndarray): image as 3-dim array : pixels_x, pixels_y, RGB
        figsize (tuple, optional): Figure size. Defaults to (100, 150).
    """

    plt.figure(figsize=figsize)
    plt.imshow(image_array, interpolation="nearest")
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show(block=False)


def plot_multiple_images(images_array: np.ndarray, figsize=(100, 150)) -> None:
    """Plot multiple images as supbplots in a single figure

    Args:
        images_array (np.ndarray): multiple images as a 5-dim array: tiles_x, tiles_y, pixels_x, pixels_y, RGB
        figsize (tuple, optional): Figure size. Defaults to (100, 150).
    """
    nrows = images_array.shape[0]
    ncols = images_array.shape[1]
    # increase by 1 if dim is 0. For plotting purposes
    nrows_fig = nrows + 1 if nrows == 1 else nrows
    ncols_fig = ncols + 1 if ncols == 1 else ncols

    _, ax = plt.subplots(
        figsize=figsize,
        nrows=nrows_fig,
        ncols=ncols_fig,
        sharex="all",
        sharey="all",
    )

    for ix in range(nrows):
        for iy in range(ncols):
            tile_single = images_array[ix, iy, :, :, :]
            ax[ix, iy].imshow(tile_single, interpolation="nearest")
            ax[ix, iy].set_xticklabels([])
            ax[ix, iy].set_yticklabels([])
    # plt.tight_layout()
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show(block=False)


def load_merge_tiles(
    path_tiles_folder: str,
    image_shape: Tuple[int, int, int],
    tile_x_first: int,
    tile_x_last: int,
    tile_y_first: int,
    tile_y_last: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Load tiles in a given range, append them together and then merge them in one 3-dim array (ie single image)

    Args:
        tile_x_first (int): [description]
        tile_x_last (int): [description]
        tile_y_first (int): [description]
        tile_y_last (int): [description]

    Returns:
        Tuple[np.ndarray, np.ndarray, int]:
        np.ndarray #1 : merged tiles in a 3-d array: pixels_x, pixels_y, RGB
        np.ndarray #2 : non-merged appended tiles as a 5-d array: tiles_x, tiles_y, pixels_x, pixels_y, RGB
    """

    tiles_y_list = list(range(tile_y_first, tile_y_last))
    tiles_x_list = list(range(tile_x_first, tile_x_last))
    len_group = len(tiles_y_list)
    # Initialize
    tiles_appended = np.zeros((len_group,) + (len_group,) + image_shape).astype(int)

    for iy, tl_y in enumerate(tiles_y_list):
        for ix, tl_x in enumerate(tiles_x_list):
            # if iy == 0:
            #     assert False
            path_tmp = os.path.join(path_tiles_folder, str(tl_x), str(tl_y) + ".jpeg")
            if os.path.isfile(path_tmp):
                image_tmp = Image.open(path_tmp)
                # plt.figure(figsize=(5,5))
                # plt.imshow(np.asarray(image_tmp))
                # plt.show(block=False)
                tiles_appended[iy, ix, :, :, :] = np.asarray(image_tmp)
    tiles_merged = np.concatenate(tiles_appended, axis=1)  # along x-axis
    tiles_merged = np.concatenate(tiles_merged, axis=1)  # along y-axis
    # plot_single_image(tiles_merged, figsize=(25, 25))

    return tiles_merged, tiles_appended


def create_map_w_tile_indices(
    tile_x_first: int,
    tile_x_last: int,
    tile_y_first: int,
    tile_y_last: int,
) -> List:
    """Creates an len(x)xlen(y) list with x & y tile-indices for each corresponding tile"""
    ## create
    tiles_x_list = list(range(tile_x_first, tile_x_last))
    tiles_y_list = list(range(tile_y_first, tile_y_last))
    len_tl_list = len(tiles_x_list)
    # initialize a 5*5 list with zeros
    map_tile_indices = [[0 for _ in range(len_tl_list)] for _ in range(len_tl_list)]
    # loop and save tile_y and tile_x indices
    for ity, ty in enumerate(tiles_y_list):
        for itx, tx in enumerate(tiles_x_list):
            map_tile_indices[ity][itx] = [ty, tx]
    return map_tile_indices


def create_square_tiles(image: np.ndarray, tile_width: int) -> np.ndarray:
    """Create square tiles of an image

    Args:
        image (np.array): input image as a 3-dim array: pixels_x, pixels_y, RGB
        tile_width (int): width of tile

    Returns:
        np.array: tiles have two extra dimensions: tile_x(dim0), tile_y(dim1)
    """

    #  First split along y axis
    # new dimenisons 1-4: tiles_y, pixels_x, pixels_y, RGB)
    tiles = np.array(np.split(image, image.shape[1] // tile_width, axis=1))

    # Then also splitting along the x axis
    # new dimenisons 1-5: tiles_x, tiles_y, pixels_x, pixels_y, RGB)
    # note: input axis is again 1 because previous step added one dimension => rows is now dim=1
    tiles = np.array(np.split(tiles, tiles.shape[1] // tile_width, axis=1))
    return tiles


def select_tile(
    images_array: np.ndarray, info: dict, figsize=(100, 150)
) -> Dict[str, List]:
    """Interactive: Plot multiple images as supbplots -> asks for selecting one subplot

    Args:
        images_array (np.ndarray): multiple images as a 5-dim array: tiles_x, tiles_y, pixels_x, pixels_y, RGB
        figsize (tuple, optional): Figure size. Defaults to (100, 150)
        image_size(string, optional): Just to plot on title of figure if these are shifted images or not
    """
    nrows = images_array.shape[0]
    ncols = images_array.shape[1]

    # increase by 1 if dim is 0. For plotting purposes
    nrows_fig = nrows + 1 if nrows == 1 else nrows
    ncols_fig = ncols + 1 if ncols == 1 else ncols

    fig, ax = plt.subplots(
        figsize=figsize,
        nrows=nrows_fig,
        ncols=ncols_fig,
        sharex="all",
        sharey="all",
    )

    selected_tile = {}
    # selected_tile["coord"] = [None, None]  # initialize
    selected_tile["coord"] = []  # list of coordinates

    def onpick(event):
        # this is to return selected plot x,y indices
        # global clicked_subplot  # , event_x
        clicked_subplot = [None, None]
        # event_x = event
        # assert False

        # Establish that at beginning all axes are as default
        for irow in range(nrows):
            for icol in range(ncols):
                for axis in ["top", "bottom", "left", "right"]:
                    ax[irow, icol].spines[axis].set_linewidth(0.5)  # default linewidth
                    ax[irow, icol].spines[axis].set_color("black")  # default color

        # (if right click) Check which plot is clicked
        if event.mouseevent.button.value == 1:

            # Initially, set in green all the tiles I already selected
            for sel_tiles in selected_tile["coord"]:
                for axis in ["top", "bottom", "left", "right"]:
                    ax[sel_tiles[0], sel_tiles[1]].spines[axis].set_linewidth(4)
                    ax[sel_tiles[0], sel_tiles[1]].spines[axis].set_color("lawngreen")

            for irow in range(nrows):
                for icol in range(ncols):
                    if event.artist == ax[irow, icol]:
                        print(
                            f"Picked subplot on row {irow} and column {icol}"
                        )  # displayed on terminal
                        clicked_subplot = [irow, icol]  # save x,y indices of plot
                        # Highlight selected plot
                        for axis in ["top", "bottom", "left", "right"]:
                            ax[irow, icol].spines[axis].set_linewidth(4)
                            ax[irow, icol].spines[axis].set_color("red")

                        # Ask if this user is sure.
                        fig.suptitle(
                            f"[{ref_string}]. You selected subplot on row {irow} and column {icol}. If this is correct -> double click on subplot"
                        )
                        fig.canvas.draw()
                        break

        # If double-click turn selected subplot's axes green, ask user to close figure
        if event.mouseevent.dblclick:
            selected_tile["coord"].append(clicked_subplot)
            for sel_tiles in selected_tile["coord"]:
                for axis in ["top", "bottom", "left", "right"]:
                    ax[sel_tiles[0], sel_tiles[1]].spines[axis].set_linewidth(4)
                    ax[sel_tiles[0], sel_tiles[1]].spines[axis].set_color("lawngreen")

            fig.suptitle(
                f"[{ref_string}]. Final choice: row {clicked_subplot[0]} and column {clicked_subplot[1]}. Please close figure."
            )

            fig.canvas.draw()
            # displayed on terminal
            print(
                f"FINAL: Picked subplot on row {clicked_subplot[0]} and column {clicked_subplot[1]}"
            )
            # plt.close()

        # If middle or right click -> no tile with target
        # code for middle & right click on my OS (GM, ubuntu) is 2 & 3
        if event.mouseevent.button.value in [2, 3]:
            clicked_subplot = [None, None]
            fig.suptitle(
                f"[{ref_string}]. No match was found :(. Please exit the figure."
            )
            fig.canvas.draw()

            # selected_tile["coord"] = clicked_subplot
            select_tile["coord"] = []

    # Plot subplots
    for ix in range(nrows):
        for iy in range(ncols):
            tile_single = images_array[ix, iy, :, :, :]
            ax[ix, iy].imshow(tile_single, interpolation="nearest")
            ax[ix, iy].set_xticklabels([])
            ax[ix, iy].set_yticklabels([])
    # plt.tight_layout()
    # manager = plt.get_current_fig_manager()
    # manager.window.showMaximized()
    id = info["id"]
    count_tbl = info["count_tbl"]
    ref_string = f"Current ID :{id}, Tables found:{count_tbl}"
    plt.suptitle(
        f"[{ref_string}]. Select the tile that contains a table tennis with right click. If none, click middle or right mouse button over any subplot."
    )

    # Make axes accessible to picker
    for irow in range(nrows):
        for icol in range(ncols):
            ax[irow, icol].set_picker(True)

    fig.canvas.mpl_connect("pick_event", onpick)
    plt.show(block=True)

    return selected_tile


# MAIN

foldername_tiles = r"/home/geomi/gm/projects/dsr/portfolio_project/MapTilesDownloader/src/output/bing_test/20"
path_positive_tiles = (
    r"/home/geomi/gm/projects/dsr/portfolio_project/trainingdata/positive_tiles"
)

path_lat_long_reference = (
    r"/home/geomi/gm/projects/dsr/portfolio_project/publicpingpong/data"
)
zoom = 20


df_table = pd.read_csv(os.path.join(path_lat_long_reference, "lat_long.csv"))

# Transform latitude to tile_y & longitude to tile_X
df_table["tile_y"] = df_table.loc[:, "latitude"].apply(lambda y: lat2tile(y, zoom))
df_table["tile_x"] = df_table.loc[:, "longitude"].apply(lambda x: long2tile(x, zoom))

# Shift types: "": no shift, r: horizontal-right, b:vertical-bottom, rb: both
shift_types = ["r", "b", "rb"]
shift_types_dict_short_long = {"r": "_shift_r", "b": "_shift_b", "rb": "_shift_rb"}

tables_info = df_table[["id", "tile_y", "tile_x"]].values.astype(int).tolist()
# path to save id of last inspected table
path_last_id = (
    r"/home/geomi/gm/projects/dsr/portfolio_project/search_current_status.txt"
)

# Load id of last inspected table & number of tables found
# if no such file -> start from first table in list
if os.path.isfile(path_last_id):
    f = open(path_last_id, "rb")
    id_last, count_tables_found = pickle.load(f)
    f.close()
else:
    id_last = tables_info[0][0]
    count_tables_found = 0

all_ids = [table[0] for table in tables_info]
index_last = all_ids.index(id_last)
tables_info_curr = tables_info[index_last:]

# flag = True

for id, tile_y, tile_x in tables_info_curr:

    # if flag == True:
    #     assert False

    print(tile_y, tile_x)

    # Path to tile
    path_to_original_tile = os.path.join(
        foldername_tiles, str(tile_x), str(tile_y) + ".jpeg"
    )

    # Look for a table only if the central tile exists
    if os.path.isfile(path_to_original_tile):

        # Load tile
        image_centre = Image.open(path_to_original_tile)

        # 1. CREATE CANVAS OF 9 REPRESENTATIVE TILES AROUND CENTRAL
        # 1.1. LOAD 5*5 TILES CENTRED ON CENTRAL TILE AND MERGE THEM
        # 1.2. SHIFT (ON THE FLY, DIRs: h, v, hv) & GET TILES-OF-INTEREST(TOIs) FROM EACH SHIFTED GROUP OF TILES
        # alterative to 1.1-1.2 : Load tiles-of-interest (original + shifted) from memory
        # In this case shifting of all tiles should be performed before
        # 1.3. PLOT TOIs, SELECT ONE WITH TARGET
        # 1.4. SAVE SELECTED TILE

        # 1.1. LOAD 5*5 TILES AROUND CENTRAL TILE AND MERGE THEM
        tile_x_first = tile_x - 2
        tile_x_last = tile_x + 3  # want +2, use +3 because last is not included
        tile_y_first = tile_y - 2
        tile_y_last = tile_y + 3
        image_shape = np.asarray(image_centre).shape

        tiles_merged, tiles_unmerged = load_merge_tiles(
            foldername_tiles,
            image_shape,
            tile_x_first,
            tile_x_last,
            tile_y_first,
            tile_y_last,
        )

        # 1.2. SHIFT (r, b, rb) & GET TILES-OF-INTEREST(TOIs) FROM EACH SHIFTED GROUP OF TILES

        # Save indices of tile_x, tile_y the 5*5 canvas we create
        map_tile_indices = create_map_w_tile_indices(
            tile_x_first, tile_x_last, tile_y_first, tile_y_last
        )

        # For each shift-type: define difference in the number of tile_x & tile_y from original
        x_dif_from_orig = {"r": 0, "b": -1, "rb": -1}
        y_dif_from_orig = {"r": -1, "b": 0, "rb": -1}

        # Coordinates of TOIs relative to the corresponding shifted group of tiles

        # Dimensions for shifted group of tiles are:
        # r: 5x4, b: 4x5, rb: 4x4
        # eg. "r": [2, 1] means -> from the 5x4 tiles after shifting right -> get tile in position [2,1]
        coords_tois_onshifted = {
            "r": [[2, 1], [2, 2]],
            "b": [[1, 2], [2, 2]],
            "rb": [[1, 1], [1, 2], [2, 1], [2, 2]],
        }

        # We want to have 3x3 tiles to inspect, with original tile + 8 shifted around it.
        # For each defined TOI above define corresponding position in the new 3x3 tiles group
        # [1,1] will be filled by original central tile
        coords_tois_onnew = {
            "r": [[1, 0], [1, 2]],
            "b": [[0, 1], [2, 1]],
            "rb": [[0, 0], [0, 2], [2, 0], [2, 2]],
        }

        width_tile = image_shape[0]
        # Initialize matrix for new 3x3 tiles group
        len_new_plot = 3
        tiles_group_plot = np.zeros(
            (len_new_plot,) + (len_new_plot,) + image_shape
        ).astype(int)

        # Add original central tile in middle
        tiles_group_plot[1, 1, :, :, :] = np.asarray(image_centre)

        for shift_fly in shift_types:
            coord_tois_onshifted = coords_tois_onshifted[shift_fly]
            coord_tois_onnew = coords_tois_onnew[shift_fly]

            xdim_orig, y_dim_orig, _ = tiles_merged.shape
            if shift_fly == "r":
                tile_x_range = [0, xdim_orig]
                tile_y_range = [width_tile // 2, -width_tile // 2]
            elif shift_fly == "b":
                tile_x_range = [width_tile // 2, -width_tile // 2]
                tile_y_range = [0, y_dim_orig]
            elif shift_fly == "rb":
                tile_x_range = [width_tile // 2, -width_tile // 2]
                tile_y_range = [width_tile // 2, -width_tile // 2]

            # Cut left-right and/or top-bottom edges of merged-tiles, by half the width of a tile
            tiles_merged_cut = tiles_merged[
                tile_x_range[0] : tile_x_range[1], tile_y_range[0] : tile_y_range[1], :
            ]

            # Inspect
            # should be shorter at y_edges in "r", x_edges in "b", and at both edges with "rb"
            # plot_single_image(tiles_merged_cut)

            # Create square tiles with dims same as original tiles
            tiles_shifted = create_square_tiles(tiles_merged_cut, width_tile)

            # Get TOIs add them to new tiles_group
            for coord_shift, coord_new in zip(coord_tois_onshifted, coord_tois_onnew):
                irow_n = coord_new[0]
                icol_n = coord_new[1]
                irow_sh = coord_shift[0]
                icol_sh = coord_shift[1]
                tiles_group_plot[irow_n, icol_n, :, :, :] = tiles_shifted[
                    irow_sh, icol_sh, :, :, :
                ]
        # Inspect
        # plot_multiple_images(tiles_group_plot)

        # 1.3. PLOT TOIs, SELECT ONE WITH TARGET (if any)

        info = {"id": id, "count_tbl": count_tables_found}
        tile_coords = select_tile(tiles_group_plot, info)
        tile_coords_list = tile_coords["coord"]
        # if id ==1:
        #     assert False

        # 1.4. SAVE SELECTED TILE (if any)

        # if tile_coords != [None, None]:
        if len(tile_coords_list) != 0:
            # if flag == True:
            #     assert False
            for tile_coord in tile_coords_list:
                # Get shift-type of selected title
                shift_of_selected_tile = None
                for key, values in coords_tois_onnew.items():
                    # assert False
                    if tile_coord in values:
                        shift_of_selected_tile = key
                        # Find coords in shifted image
                        # get index in TOI coords for shift-type
                        index = values.index(tile_coord)
                        # use same index for coords in shifted-tiles-group
                        coord_shift = coords_tois_onshifted[key][index]
                        # Find tile_x, tile_y corresponding to selected image
                        # first crop map-with cordinates so is matching the shifted-tiles-group
                        x_dif = x_dif_from_orig[key]
                        y_dif = y_dif_from_orig[key]
                        # crop on x dim
                        # if x_dif is 0, return the whole map
                        coord_map = (
                            map_tile_indices[:x_dif] if x_dif != 0 else map_tile_indices
                        )
                        # crop on y dim
                        if y_dif != 0:
                            coord_map = [row_list[:y_dif] for row_list in coord_map]
                        else:
                            # if y_dif = 0 , keep all
                            pass
                        # extract coords from croped map
                        coord_selected = coord_map[coord_shift[0]][coord_shift[1]]
                        shift_str = shift_types_dict_short_long[key]
                        break
                    else:
                        pass

                # it's the original tile, no shift
                if shift_of_selected_tile is None:
                    shift_str = ""
                    coord_selected = [tile_y, tile_x]

                # Get selected tile based on coords
                selected_tile = tiles_group_plot[tile_coord[0], tile_coord[1], :, :, :]
                im = Image.fromarray(selected_tile.astype(np.uint8))
                # im.show()
                tile_y_save = coord_selected[0]
                tile_x_save = coord_selected[1]
                filename = (
                    f"{str(zoom)}_{str(tile_x_save)}_{str(tile_y_save)}{shift_str}.jpeg"
                )
                im.save(os.path.join(path_positive_tiles, filename))
                print("Saved selected tile")
                count_tables_found += 1

        else:
            print("No target was found around this candidate tile")
            pass
    else:
        print("No saved map tile for this reference table")
        pass

    # Save id of last table inspected + number of tables found
    id_n_tablecount = [id, count_tables_found]
    f = open(path_last_id, "wb")
    pickle.dump(id_n_tablecount, f)
    f.close()
