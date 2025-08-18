"""CLI entry point that delegates to __main__.py"""

def main():
    """Main CLI entry point - delegates to __main__.py"""
    from . import __main__
    __main__.main()

if __name__ == "__main__":
    main()
