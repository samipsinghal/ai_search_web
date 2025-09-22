from .controller import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("controller.main() not implemented yet — skeleton OK.", e)
