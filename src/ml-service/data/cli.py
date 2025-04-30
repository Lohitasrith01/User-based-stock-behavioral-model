import argparse
import logging
from datetime import datetime, timedelta
from data_pipeline import DataPipeline

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description='Stock Market Data Pipeline')
    
    # Add arguments
    parser.add_argument('--symbols', nargs='+', required=True,
                      help='List of stock symbols to collect data for')
    parser.add_argument('--start-date', type=str,
                      help='Start date for data collection (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                      help='End date for data collection (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, default='../config.json',
                      help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize pipeline
        pipeline = DataPipeline(config_path=args.config)
        
        # Set default dates if not provided
        if not args.start_date:
            args.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not args.end_date:
            args.end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Run pipeline
        logger.info(f"Starting data pipeline for symbols: {args.symbols}")
        logger.info(f"Date range: {args.start_date} to {args.end_date}")
        
        pipeline.run_pipeline(args.symbols)
        
        logger.info("Data pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Error running data pipeline: {str(e)}")
        raise

if __name__ == '__main__':
    main() 