function main(params) {
  if (params.name) {
    return { greeting: `Hello ${params.name}` };
  }
  return { greeting: 'Hello World' };
}

exports.main = main;
