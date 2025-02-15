#! python

from argparse import ArgumentParser
from hydromosaic.indexing.index_netCDF import index_directory


def index(): 
#if __name__ == "__main__":
    parser = ArgumentParser(
        description = "Index netCDF files into hydromosaic database"
        )
    parser.add_argument("-d", "--dsn", help="connection string for database")
    parser.add_argument("-l", "--log_level", help='level of logging detail', default="info", choices=["debug", "info", "warning", "error", "critical"])
    parser.add_argument("-p", "--metadata_prefix", help="prefix for GCM metadata", default="downscaling_GCM_")
    parser.add_argument("directory", help="directory to index")
    args = parser.parse_args()
    
    
    index_directory(dsn = args.dsn, directory = args.directory, log_level=args.log_level, gcm_prefix = args.metadata_prefix)