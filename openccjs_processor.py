# get the full.js from current directory then get the content of STPhrases
# then delimit by |



def process_st_phrases():
    # Step 1: Read the full.js file
    with open('full.js', 'r', encoding='utf-8') as file:
        content = file.read()

    # Step 2: Extract the content of STPhrases
    start = content.find('STPhrases = "') + len('STPhrases = "')
    end = content.find('";', start)
    st_phrases_content = content[start:end]

    # Step 3: Delimit by '|'
    phrases_list = st_phrases_content.split('|')

    # Step 4: For each item, delimit by whitespace and list the second element
    second_elements = [phrase.split()[1] for phrase in phrases_list if len(phrase.split()) > 1]

    # Combine all second elements into one string
    combined_string = ''.join(second_elements)

    # Get all unique characters in the string
    unique_chars = set(combined_string)

    return unique_chars

# Example usage
if __name__ == "__main__":
    result = process_st_phrases()
    print(result)
    def is_substring(substring, string):
        return substring in string

    # Example usage
    main_string = "Hello, world!"
    sub_string = "world"
    print(is_substring(sub_string, main_string))  # Output: True

    sub_string = "Python"
    print(is_substring(sub_string, main_string))  # Output: False
