from m3u8 import create_app
def main():
    app = create_app()
    app.run(debug=True)
if __name__ == "__main__":
    main()
