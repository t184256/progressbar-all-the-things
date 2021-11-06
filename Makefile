.PHONY: lint nix-tests
.PHONY: lint-flake8 lint-codespell lint-spdx-check
.PHONY: check clean

check: lint

lint: lint-flake8 lint-codespell lint-spdx-check

lint-flake8:
	flake8

lint-codespell:
	codespell

COPYRIGHT=SPDX-FileCopyrightText: 2021 Alexander Sosedkin <monk@unboiled.info>
LICENSE=SPDX-License-Identifier: GPL-3.0-only
lint-spdx-check:
	@echo spdx-check
	@(find . -name '*.py'; find . -name '*.sh') | \
	while IFS= read -r FILE; do \
		if [ $$(wc -c < $$FILE) = 0 ]; then \
			echo "  not checking SPDX tags of empty $$FILE."; \
			continue; \
		fi; \
		echo -n "  checking SPDX tags of $$FILE: "; \
		if ! grep -q "# ${COPYRIGHT}$$" $$FILE; then \
			echo "NO ${COPYRIGHT}"; exit 1; \
		fi; \
		if ! grep -q "# ${COPYRIGHT}$$" $$FILE; then \
			echo "NO ${LICENSE}"; exit 1; \
		fi; \
		echo 'OK'; \
	done
	@echo '  SPDX tags of Python files are in order.'

nix-tests:
	nix run .
	nix flake check
