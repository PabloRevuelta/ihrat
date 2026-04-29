import bathtub_module
import geopandas as gpd

if __name__ == "__main__":

    # Example 1: Run bathtub module with a single TWL value for one scenario
    twl_dic_single={'scen 1': 1.0}
    coastlines_file_name = 'coastlines.shp'
    crs = 'epsg:3035'
    bathtub_module.bathtub_module(twl_dic_single, coastlines_file_name, crs, input_type='single value')
    
    
    # Example 2: Run bathtub module with multiple scenarios from a point shapefile
    # TWL values will be interpolated using IDW
    twl_dic_multi={'file_name':'ExpFit_A_pilot','scens_names': ['exp_rp50','exp_rp100']}
    coastlines_file_name='coastlines.shp'
    crs='epsg:3035'
    bathtub_module.bathtub_module(twl_dic_multi,coastlines_file_name,crs,input_type='multi value')

    # Example 3: Batch processing for multiple municipalities (communes)
    # Reads a GeoJSON with commune boundaries, iterates through each unique commune,
    # and runs the flooding analysis using specific MDT files for each one.
    gdf_communes=gpd.read_file(r"C:\Users\revueltaap\Desktop\communes map.geojson")
    lista_munis = gdf_communes["Communes"].unique().tolist()
    for muni in lista_munis:
        muni=muni.strip()

        twl_dic_multi={'file_name':f'TWL_points_scens{muni}','scens_names':
            [ '1', '5', '10', '50', '100', '500',
             '1_126_05_2050', '5_126_05_2050', '10_126_05_2050', '50_126_05_2050', '100_126_05_2050', '500_126_05_2050',
             '1_126_05_2080', '5_126_05_2080', '10_126_05_2080', '50_126_05_2080', '100_126_05_2080', '500_126_05_2080',
             '1_126_50_2050', '5_126_50_2050', '10_126_50_2050', '50_126_50_2050', '100_126_50_2050', '500_126_50_2050',
             '1_126_50_2080', '5_126_50_2080', '10_126_50_2080', '50_126_50_2080', '100_126_50_2080', '500_126_50_2080',
             '1_126_95_2050', '5_126_95_2050', '10_126_95_2050', '50_126_95_2050', '100_126_95_2050', '500_126_95_2050',
             '1_126_95_2080', '5_126_95_2080', '10_126_95_2080', '50_126_95_2080', '100_126_95_2080', '500_126_95_2080',
             '1_245_05_2050', '5_245_05_2050', '10_245_05_2050', '50_245_05_2050', '100_245_05_2050', '500_245_05_2050',
             '1_245_05_2080', '5_245_05_2080', '10_245_05_2080', '50_245_05_2080', '100_245_05_2080', '500_245_05_2080',
             '1_245_50_2050', '5_245_50_2050', '10_245_50_2050', '50_245_50_2050', '100_245_50_2050', '500_245_50_2050',
             '1_245_50_2080', '5_245_50_2080', '10_245_50_2080', '50_245_50_2080', '100_245_50_2080', '500_245_50_2080',
             '1_245_95_2050', '5_245_95_2050', '10_245_95_2050', '50_245_95_2050', '100_245_95_2050', '500_245_95_2050',
             '1_245_95_2080', '5_245_95_2080', '10_245_95_2080', '50_245_95_2080', '100_245_95_2080', '500_245_95_2080',
             '1_585_05_2050', '5_585_05_2050', '10_585_05_2050', '50_585_05_2050', '100_585_05_2050', '500_585_05_2050',
             '1_585_05_2080', '5_585_05_2080', '10_585_05_2080', '50_585_05_2080', '100_585_05_2080', '500_585_05_2080',
             '1_585_50_2050', '5_585_50_2050', '10_585_50_2050', '50_585_50_2050', '100_585_50_2050', '500_585_50_2050',
             '1_585_50_2080', '5_585_50_2080', '10_585_50_2080', '50_585_50_2080', '100_585_50_2080', '500_585_50_2080',
             '1_585_95_2050', '5_585_95_2050', '10_585_95_2050', '50_585_95_2050', '100_585_95_2050', '500_585_95_2050',
             '1_585_95_2080', '5_585_95_2080', '10_585_95_2080', '50_585_95_2080', '100_585_95_2080', '500_585_95_2080']
        }
        crs='epsg:3395'
        bathtub_module.bathtub_module(twl_dic_multi, 'ref_coastlines.geojson', crs, input_type='multi value',mdt_filename='mdt_'+muni+'.tif',idw_files=True)

