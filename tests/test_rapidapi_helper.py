from helpers.rapidapi_helper import RapidAPIHelper
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rapidapi_helper():
    helper = RapidAPIHelper()
    
    # Test with a valid profile
    valid_profile_url = "https://www.linkedin.com/in/ACwAAAFSIEMBoXWcPvTJrYDORXdCK4mitvAgi04"
    logger.info(f"Testing RapidAPIHelper with valid profile URL: {valid_profile_url}")
    result = helper.get_linkedin_profile(valid_profile_url)
    if result:
        logger.info("Successfully retrieved LinkedIn profile data")
        logger.debug(f"Processed LinkedIn Data: {result}")
    else:
        logger.error("Failed to retrieve LinkedIn profile data")

    # Test with an invalid profile URL
    invalid_url = "https://www.linkedin.com/in/this-profile-does-not-exist"
    logger.info(f"Testing RapidAPIHelper with invalid profile URL: {invalid_url}")
    invalid_result = helper.get_linkedin_profile(invalid_url)
    if invalid_result is None:
        logger.info("Correctly handled invalid profile URL")
    else:
        logger.warning(f"Unexpectedly retrieved data for invalid URL: {invalid_result}")

    # Test with a malformed URL
    malformed_url = "not-a-url"
    logger.info(f"Testing RapidAPIHelper with malformed URL: {malformed_url}")
    malformed_result = helper.get_linkedin_profile(malformed_url)
    if malformed_result is None:
        logger.info("Correctly handled malformed URL")
    else:
        logger.warning(f"Unexpectedly retrieved data for malformed URL: {malformed_result}")

if __name__ == "__main__":
    test_rapidapi_helper()